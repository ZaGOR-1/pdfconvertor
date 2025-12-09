"""
Тести продуктивності та оптимізації
==================================

Тестування швидкодії, використання пам'яті та ресурсів
"""

import unittest
import time
import tracemalloc
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from converter.doc_converter import DocConverter
from utils.config import ConfigManager
from utils.logger import Logger


class TestPerformance(unittest.TestCase):
    """Тести продуктивності"""
    
    def setUp(self):
        """Налаштування перед кожним тестом"""
        self.temp_dir = tempfile.mkdtemp()
        tracemalloc.start()
        
    def tearDown(self):
        """Очищення після кожного тесту"""
        tracemalloc.stop()
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_converter_initialization_speed(self):
        """Тест швидкості ініціалізації конвертера"""
        start_time = time.time()
        
        converter = DocConverter()
        
        elapsed = time.time() - start_time
        
        # Ініціалізація має бути швидкою (< 0.1 сек)
        self.assertLess(elapsed, 0.1, 
                       f"Ініціалізація занадто повільна: {elapsed:.3f}s")
    
    def test_config_load_speed(self):
        """Тест швидкості завантаження конфігурації"""
        start_time = time.time()
        
        config = ConfigManager()
        value = config.get("theme")
        
        elapsed = time.time() - start_time
        
        # Завантаження конфігу має бути швидким (< 0.05 сек)
        self.assertLess(elapsed, 0.05,
                       f"Завантаження конфігу повільне: {elapsed:.3f}s")
    
    def test_memory_usage_converter(self):
        """Тест використання пам'яті конвертером"""
        # Отримуємо поточне використання пам'яті
        tracemalloc.reset_peak()
        
        converter = DocConverter()
        
        # Отримуємо пікове використання
        current, peak = tracemalloc.get_traced_memory()
        peak_mb = peak / 1024 / 1024
        
        # Конвертер не повинен займати більше 50 MB
        self.assertLess(peak_mb, 50,
                       f"Конвертер використовує забагато пам'яті: {peak_mb:.2f} MB")
    
    def test_logger_performance(self):
        """Тест продуктивності логування"""
        logger = Logger()
        
        start_time = time.time()
        
        # Логуємо 100 повідомлень
        for i in range(100):
            logger.info(f"Test message {i}")
        
        elapsed = time.time() - start_time
        
        # 100 записів повинні виконатися швидко (< 0.1 сек)
        self.assertLess(elapsed, 0.1,
                       f"Логування повільне: {elapsed:.3f}s для 100 записів")


class TestResourceUsage(unittest.TestCase):
    """Тести використання ресурсів"""
    
    def test_file_handles_cleanup(self):
        """Тест закриття файлових дескрипторів"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_handles = process.num_handles() if hasattr(process, 'num_handles') else 0
        
        # Створюємо та закриваємо конвертер кілька разів
        for _ in range(5):
            converter = DocConverter()
            del converter
        
        final_handles = process.num_handles() if hasattr(process, 'num_handles') else 0
        
        # Кількість дескрипторів не повинна зростати суттєво
        handle_growth = final_handles - initial_handles
        self.assertLess(abs(handle_growth), 10,
                       f"Витік файлових дескрипторів: +{handle_growth}")


class TestScalability(unittest.TestCase):
    """Тести масштабованості"""
    
    def setUp(self):
        """Налаштування перед кожним тестом"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Очищення після кожного тесту"""
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_handle_many_files(self):
        """Тест обробки великої кількості файлів"""
        # Створюємо 50 тимчасових файлів
        files = []
        for i in range(50):
            temp_file = Path(self.temp_dir) / f"test_{i}.docx"
            temp_file.write_text(f"Test content {i}")
            files.append(temp_file)
        
        start_time = time.time()
        
        # Тестуємо тільки збір файлів (без конвертації)
        from converter.file_handler import FileHandler
        valid_files = [f for f in files if FileHandler.is_word_file(f)]
        
        elapsed = time.time() - start_time
        
        # Перевірка 50 файлів має бути швидкою (< 1 сек)
        self.assertLess(elapsed, 1.0,
                       f"Обробка 50 файлів повільна: {elapsed:.3f}s")
        self.assertEqual(len(valid_files), 50)


class TestCacheOptimization(unittest.TestCase):
    """Тести оптимізації кешування"""
    
    def test_config_singleton(self):
        """Тест що ConfigManager є Singleton"""
        config1 = ConfigManager()
        config2 = ConfigManager()
        
        # Обидва екземпляри мають бути одним об'єктом
        self.assertIs(config1, config2,
                     "ConfigManager не є Singleton")
    
    def test_logger_singleton(self):
        """Тест що Logger є Singleton"""
        logger1 = Logger()
        logger2 = Logger()
        
        # Обидва екземпляри мають бути одним об'єктом
        self.assertIs(logger1, logger2,
                     "Logger не є Singleton")


if __name__ == '__main__':
    print("=" * 70)
    print("Запуск тестів продуктивності...")
    print("=" * 70)
    
    # Запуск тестів з детальним виводом
    unittest.main(verbosity=2)
