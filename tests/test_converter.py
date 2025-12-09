"""
Тести для модуля конвертації документів
========================================

Функціональне тестування конвертера Word → PDF
"""

import unittest
from pathlib import Path
import tempfile
import os
import sys

# Додаємо батьківську директорію до шляху для імпорту
sys.path.insert(0, str(Path(__file__).parent.parent))

from converter.doc_converter import DocConverter
from converter.file_handler import FileHandler


class TestDocConverter(unittest.TestCase):
    """Тести для DocConverter"""
    
    def setUp(self):
        """Налаштування перед кожним тестом"""
        self.converter = DocConverter()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Очищення після кожного тесту"""
        # Видалення тимчасової директорії
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_converter_initialization(self):
        """Тест ініціалізації конвертера"""
        self.assertIsNotNone(self.converter)
        self.assertIsInstance(self.converter.compression_settings, dict)
        
    def test_invalid_file_path(self):
        """Тест обробки неіснуючого файлу"""
        fake_path = Path("nonexistent_file.docx")
        success, message = self.converter.convert_to_pdf(fake_path)
        
        self.assertFalse(success)
        self.assertIn("не знайдено", message.lower())
    
    def test_unsupported_format(self):
        """Тест обробки непідтримуваного формату"""
        # Створюємо тимчасовий файл з неправильним розширенням
        temp_file = Path(self.temp_dir) / "test.txt"
        temp_file.write_text("Test content")
        
        success, message = self.converter.convert_to_pdf(temp_file)
        
        self.assertFalse(success)
        self.assertIn("непідтримуваний", message.lower())


class TestFileHandler(unittest.TestCase):
    """Тести для FileHandler"""
    
    def setUp(self):
        """Налаштування перед кожним тестом"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Очищення після кожного тесту"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_is_word_file_valid_docx(self):
        """Тест перевірки DOCX файлу"""
        temp_file = Path(self.temp_dir) / "test.docx"
        temp_file.write_text("test")
        
        result = FileHandler.is_word_file(temp_file)
        self.assertTrue(result)
    
    def test_is_word_file_valid_doc(self):
        """Тест перевірки DOC файлу"""
        temp_file = Path(self.temp_dir) / "test.doc"
        temp_file.write_text("test")
        
        result = FileHandler.is_word_file(temp_file)
        self.assertTrue(result)
    
    def test_is_word_file_invalid(self):
        """Тест перевірки не-Word файлу"""
        temp_file = Path(self.temp_dir) / "test.txt"
        temp_file.write_text("test")
        
        result = FileHandler.is_word_file(temp_file)
        self.assertFalse(result)
    
    def test_validate_file_nonexistent(self):
        """Тест валідації неіснуючого файлу"""
        fake_path = Path("nonexistent.docx")
        
        is_valid, error = FileHandler.validate_file(fake_path)
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_validate_file_too_large(self):
        """Тест валідації занадто великого файлу"""
        temp_file = Path(self.temp_dir) / "large.docx"
        
        # Створюємо файл розміром > 100 MB (за замовчуванням)
        with open(temp_file, 'wb') as f:
            f.write(b'0' * (101 * 1024 * 1024))  # 101 MB
        
        is_valid, error = FileHandler.validate_file(temp_file)
        
        self.assertFalse(is_valid)
        self.assertIn("великий", error.lower())
    
    def test_get_output_path_default(self):
        """Тест генерації вихідного шляху за замовчуванням"""
        input_path = Path(self.temp_dir) / "test.docx"
        input_path.write_text("test")
        
        output_path = FileHandler.get_output_path(input_path)
        
        self.assertEqual(output_path.suffix, '.pdf')
        self.assertEqual(output_path.stem, 'test')
    
    def test_get_output_path_with_auto_number(self):
        """Тест автонумерації при дублікатах"""
        input_path = Path(self.temp_dir) / "test.docx"
        input_path.write_text("test")
        
        # Створюємо існуючий PDF
        existing_pdf = Path(self.temp_dir) / "test.pdf"
        existing_pdf.write_text("existing")
        
        output_path = FileHandler.get_output_path(input_path, auto_number=True)
        
        self.assertTrue('(1)' in output_path.stem)


class TestCompressionLevels(unittest.TestCase):
    """Тести для різних рівнів стиснення"""
    
    def setUp(self):
        """Налаштування перед кожним тестом"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Очищення після кожного тесту"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_compression_level_1(self):
        """Тест рівня стиснення 1 (мінімальне)"""
        settings = {'enable_compression': True, 'compression_level': 1}
        converter = DocConverter(compression_settings=settings)
        
        self.assertEqual(converter.compression_settings['compression_level'], 1)
    
    def test_compression_level_9(self):
        """Тест рівня стиснення 9 (максимальне)"""
        settings = {'enable_compression': True, 'compression_level': 9}
        converter = DocConverter(compression_settings=settings)
        
        self.assertEqual(converter.compression_settings['compression_level'], 9)


if __name__ == '__main__':
    # Запуск тестів з детальним виводом
    unittest.main(verbosity=2)
