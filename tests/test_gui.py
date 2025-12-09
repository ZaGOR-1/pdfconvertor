"""
UI Tests - Базові тести для GUI компонентів
==========================================

Тести для перевірки функціональності GUI елементів.
"""

import unittest
from pathlib import Path
import sys
import os

# Додаємо батьківську директорію до шляху
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.localization import Localization
from utils.config import ConfigManager


class TestLocalization(unittest.TestCase):
    """Тести системи локалізації."""
    
    def setUp(self):
        """Підготовка до тестів."""
        self.i18n = Localization()
    
    def test_singleton_pattern(self):
        """Тест Singleton патерну."""
        i18n1 = Localization()
        i18n2 = Localization()
        self.assertIs(i18n1, i18n2, "Localization має бути Singleton")
    
    def test_get_existing_key(self):
        """Тест отримання існуючого ключа."""
        title = self.i18n.get("app_title")
        self.assertIsInstance(title, str)
        self.assertIn("Word to PDF", title)
    
    def test_get_nonexistent_key(self):
        """Тест отримання неіснуючого ключа."""
        result = self.i18n.get("nonexistent_key_12345")
        self.assertEqual(result, "nonexistent_key_12345")
    
    def test_formatting(self):
        """Тест форматування рядків."""
        result = self.i18n.get("status_files_added", count=5)
        self.assertIn("5", result)
    
    def test_all_required_keys_exist(self):
        """Тест наявності всіх обов'язкових ключів."""
        required_keys = [
            "app_title",
            "app_subtitle",
            "app_version",
            "btn_convert",
            "btn_clear",
            "btn_stop",
            "status_ready",
            "file_pending",
            "file_converting",
            "file_completed",
            "file_failed",
            "icon_document",
            "icon_folder",
            "icon_clip",
            "icon_download",
        ]
        
        for key in required_keys:
            with self.subTest(key=key):
                result = self.i18n.get(key)
                self.assertNotEqual(result, key, f"Ключ '{key}' не знайдено в локалізації")


class TestConfigManager(unittest.TestCase):
    """Тести менеджера конфігурації."""
    
    def setUp(self):
        """Підготовка до тестів."""
        self.config = ConfigManager()
    
    def test_singleton_pattern(self):
        """Тест Singleton патерну."""
        config1 = ConfigManager()
        config2 = ConfigManager()
        self.assertIs(config1, config2, "ConfigManager має бути Singleton")
    
    def test_get_existing_key(self):
        """Тест отримання існуючого ключа."""
        theme = self.config.get("theme")
        self.assertIn(theme, ["light", "dark"])
    
    def test_get_with_default(self):
        """Тест отримання з значенням за замовчуванням."""
        result = self.config.get("nonexistent.key", "default_value")
        self.assertEqual(result, "default_value")
    
    def test_nested_keys(self):
        """Тест отримання вкладених ключів."""
        compression = self.config.get("conversion.enable_compression", False)
        self.assertIsInstance(compression, bool)
    
    def test_get_theme(self):
        """Тест отримання теми."""
        theme = self.config.get_theme()
        self.assertIn(theme, ["light", "dark"])
    
    def test_window_geometry(self):
        """Тест отримання геометрії вікна."""
        geometry = self.config.get_window_geometry()
        self.assertIsInstance(geometry, dict)
        self.assertIn("width", geometry)
        self.assertIn("height", geometry)
        self.assertGreater(geometry["width"], 0)
        self.assertGreater(geometry["height"], 0)


class TestFileHandlerValidation(unittest.TestCase):
    """Тести валідації файлів."""
    
    def setUp(self):
        """Підготовка до тестів."""
        from converter.file_handler import FileHandler
        self.handler = FileHandler
    
    def test_is_word_file(self):
        """Тест перевірки Word файлів."""
        self.assertTrue(self.handler.is_word_file(Path("test.doc")))
        self.assertTrue(self.handler.is_word_file(Path("test.docx")))
        self.assertTrue(self.handler.is_word_file(Path("test.DOC")))
        self.assertTrue(self.handler.is_word_file(Path("test.DOCX")))
        
        self.assertFalse(self.handler.is_word_file(Path("test.pdf")))
        self.assertFalse(self.handler.is_word_file(Path("test.txt")))
        self.assertFalse(self.handler.is_word_file(Path("test.xlsx")))
    
    def test_get_file_size(self):
        """Тест форматування розміру файлу."""
        # Створюємо тимчасовий файл для тесту
        test_file = Path(__file__).parent / "temp_test.txt"
        try:
            test_file.write_text("Test content")
            size = self.handler.get_file_size(test_file)
            self.assertIsInstance(size, str)
            self.assertTrue(any(unit in size for unit in ["B", "KB", "MB"]))
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_estimate_pdf_size(self):
        """Тест оцінки розміру PDF."""
        # Створюємо тимчасовий файл
        test_file = Path(__file__).parent / "temp_test.docx"
        try:
            test_file.write_text("Test content" * 1000)
            estimated = self.handler.estimate_pdf_size(test_file)
            self.assertIsInstance(estimated, float)
            self.assertGreater(estimated, 0)
        finally:
            if test_file.exists():
                test_file.unlink()


class TestDragAndDropValidation(unittest.TestCase):
    """Тести для drag & drop функціоналу."""
    
    def test_file_extension_validation(self):
        """Тест валідації розширень файлів."""
        from converter.file_handler import FileHandler
        
        valid_extensions = [".doc", ".docx", ".DOC", ".DOCX"]
        invalid_extensions = [".pdf", ".txt", ".xlsx", ".pptx"]
        
        for ext in valid_extensions:
            test_path = Path(f"test{ext}")
            self.assertTrue(FileHandler.is_word_file(test_path))
        
        for ext in invalid_extensions:
            test_path = Path(f"test{ext}")
            self.assertFalse(FileHandler.is_word_file(test_path))


def run_ui_tests():
    """Запуск всіх UI тестів."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Додаємо всі тестові класи
    suite.addTests(loader.loadTestsFromTestCase(TestLocalization))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigManager))
    suite.addTests(loader.loadTestsFromTestCase(TestFileHandlerValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestDragAndDropValidation))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_ui_tests()
    sys.exit(0 if success else 1)
