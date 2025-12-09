"""
Система логування для Word to PDF Converter.
Логування операцій конвертації та помилок.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Optional


class Logger:
    """Singleton клас для логування подій програми."""
    
    _instance = None
    _log_dir = Path("logs")
    _log_file = "converter.log"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Ініціалізація системи логування."""
        if self._initialized:
            return
        
        self._initialized = True
        self._logger = None
        self._setup_logger()
    
    def _setup_logger(self, level: str = "INFO", max_file_size_mb: int = 10, backup_count: int = 5):
        """
        Налаштування логера з ротацією файлів.
        
        Args:
            level: Рівень логування (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            max_file_size_mb: Максимальний розмір файлу логу в МБ
            backup_count: Кількість backup файлів
        """
        # Створення директорії для логів
        self._log_dir.mkdir(exist_ok=True)
        
        # Створення логера
        self._logger = logging.getLogger("WordToPDFConverter")
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # Видалення існуючих handlers
        self._logger.handlers.clear()
        
        # Formatter для логів
        log_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File Handler з ротацією
        log_path = self._log_dir / self._log_file
        max_bytes = max_file_size_mb * 1024 * 1024  # Конвертація в байти
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(log_format)
        file_handler.setLevel(logging.DEBUG)
        self._logger.addHandler(file_handler)
        
        # Console Handler (тільки для ERROR та вище)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        console_handler.setLevel(logging.ERROR)
        self._logger.addHandler(console_handler)
        
        # Лог початку нової сесії
        self._logger.info("=" * 60)
        self._logger.info("Запуск Word to PDF Converter")
        self._logger.info(f"Сесія: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._logger.info("=" * 60)
    
    def reconfigure(self, level: Optional[str] = None, max_file_size_mb: Optional[int] = None, 
                   backup_count: Optional[int] = None):
        """
        Переконфігурація логера.
        
        Args:
            level: Новий рівень логування
            max_file_size_mb: Новий максимальний розмір файлу
            backup_count: Нова кількість backup файлів
        """
        current_level = logging.getLevelName(self._logger.level)
        
        self._setup_logger(
            level=level or current_level,
            max_file_size_mb=max_file_size_mb or 10,
            backup_count=backup_count or 5
        )
    
    def debug(self, message: str):
        """Лог на рівні DEBUG."""
        if self._logger:
            self._logger.debug(message)
    
    def info(self, message: str):
        """Лог на рівні INFO."""
        if self._logger:
            self._logger.info(message)
    
    def warning(self, message: str):
        """Лог на рівні WARNING."""
        if self._logger:
            self._logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        """
        Лог на рівні ERROR.
        
        Args:
            message: Повідомлення про помилку
            exc_info: Включити traceback exception
        """
        if self._logger:
            self._logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = False):
        """
        Лог на рівні CRITICAL.
        
        Args:
            message: Критичне повідомлення
            exc_info: Включити traceback exception
        """
        if self._logger:
            self._logger.critical(message, exc_info=exc_info)
    
    def log_conversion_start(self, file_path: str, output_path: str):
        """Лог початку конвертації файлу."""
        self.info(f"Початок конвертації: {file_path} → {output_path}")
    
    def log_conversion_success(self, file_path: str, duration: float):
        """Лог успішної конвертації."""
        self.info(f"✅ Успішно конвертовано: {file_path} (за {duration:.2f}s)")
    
    def log_conversion_error(self, file_path: str, error: str):
        """Лог помилки конвертації."""
        self.error(f"❌ Помилка конвертації {file_path}: {error}")
    
    def log_batch_start(self, file_count: int):
        """Лог початку пакетної конвертації."""
        self.info(f"🚀 Початок пакетної конвертації: {file_count} файл(ів)")
    
    def log_batch_complete(self, success: int, failed: int, duration: float):
        """Лог завершення пакетної конвертації."""
        self.info(f"✅ Пакетну конвертацію завершено: {success} успішно, {failed} помилок (за {duration:.2f}s)")
    
    def log_app_start(self):
        """Лог запуску програми."""
        self.info("🎯 Програма запущена")
    
    def log_app_exit(self):
        """Лог закриття програми."""
        self.info("👋 Програма закрита")
        self.info("=" * 60)
    
    def log_theme_change(self, new_theme: str):
        """Лог зміни теми."""
        self.info(f"🎨 Тему змінено на: {new_theme}")
    
    def log_config_save(self):
        """Лог збереження конфігурації."""
        self.debug("💾 Конфігурацію збережено")
    
    def log_config_load(self):
        """Лог завантаження конфігурації."""
        self.debug("📂 Конфігурацію завантажено")
    
    def get_log_file_path(self) -> Path:
        """Отримання шляху до файлу логів."""
        return self._log_dir / self._log_file
    
    def clear_old_logs(self, days: int = 30):
        """
        Видалення старих логів.
        
        Args:
            days: Видалити логи старші за вказану кількість днів
        """
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            deleted_count = 0
            
            for log_file in self._log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                self.info(f"🗑️ Видалено {deleted_count} старих лог-файлів")
        except Exception as e:
            self.error(f"Помилка видалення старих логів: {e}")
