"""
Менеджер конфігурації для Word to PDF Converter.
Зберігає налаштування користувача між сесіями.
"""

import json
from pathlib import Path
from typing import Any, Optional


class ConfigManager:
    """Singleton клас для управління конфігурацією програми."""
    
    _instance = None
    _config_file = Path("config.json")
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Ініціалізація менеджера конфігурації."""
        if self._initialized:
            return
        
        self._initialized = True
        self._config = self._load_default_config()
        self.load()
    
    def _load_default_config(self) -> dict:
        """
        Завантаження дефолтної конфігурації.
        
        Returns:
            Словник з дефолтними налаштуваннями
        """
        return {
            "theme": "dark",
            "window": {
                "width": 900,
                "height": 700,
                "x": None,
                "y": None
            },
            "settings_window": {
                "x": None,
                "y": None
            },
            "last_output_folder": None,
            "auto_save_config": True,
            "conversion": {
                "ask_overwrite": True,
                "show_notifications": True,
                "auto_number_files": False,
                "max_file_size_mb": 100,
                "pdf_quality": "standard",
                "orientation": "portrait",
                "page_size": "A4",
                "enable_compression": False,
                "compression_level": 6
            },
            "logging": {
                "enabled": True,
                "level": "INFO",
                "max_file_size_mb": 10,
                "backup_count": 5
            }
        }
    
    def load(self) -> bool:
        """
        Завантаження конфігурації з файлу.
        
        Returns:
            True якщо конфігурацію успішно завантажено, False інакше
        """
        try:
            if self._config_file.exists():
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Оновлюємо конфігурацію, зберігаючи дефолтні значення для нових полів
                    self._merge_config(loaded_config)
                print(f"✅ Конфігурацію завантажено з {self._config_file}")
                return True
            else:
                print(f"📝 Файл конфігурації не знайдено, використовуються дефолтні налаштування")
                return False
        except Exception as e:
            print(f"⚠️ Помилка завантаження конфігурації: {e}")
            print(f"📝 Використовуються дефолтні налаштування")
            return False
    
    def _merge_config(self, loaded_config: dict):
        """
        Об'єднання завантаженої конфігурації з дефолтною.
        
        Args:
            loaded_config: Завантажена конфігурація
        """
        def merge_dicts(default: dict, loaded: dict) -> dict:
            """Рекурсивне об'єднання словників."""
            result = default.copy()
            for key, value in loaded.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dicts(result[key], value)
                else:
                    result[key] = value
            return result
        
        self._config = merge_dicts(self._config, loaded_config)
    
    def save(self) -> bool:
        """
        Збереження конфігурації у файл.
        
        Returns:
            True якщо конфігурацію успішно збережено, False інакше
        """
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            print(f"💾 Конфігурацію збережено в {self._config_file}")
            return True
        except Exception as e:
            print(f"❌ Помилка збереження конфігурації: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Отримання значення з конфігурації.
        
        Args:
            key: Ключ (підтримує вкладені ключі через крапку, наприклад "window.width")
            default: Дефолтне значення якщо ключ не знайдено
            
        Returns:
            Значення з конфігурації або дефолтне значення
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any, auto_save: bool = True) -> bool:
        """
        Встановлення значення в конфігурації.
        
        Args:
            key: Ключ (підтримує вкладені ключі через крапку)
            value: Значення для збереження
            auto_save: Автоматично зберегти конфігурацію
            
        Returns:
            True якщо значення встановлено успішно
        """
        keys = key.split('.')
        config = self._config
        
        try:
            # Навігація до потрібного рівня
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Встановлення значення
            config[keys[-1]] = value
            
            # Автозбереження
            if auto_save and self._config.get('auto_save_config', True):
                self.save()
            
            return True
        except Exception as e:
            print(f"❌ Помилка встановлення значення '{key}': {e}")
            return False
    
    def get_theme(self) -> str:
        """Отримання поточної теми."""
        return self.get('theme', 'dark')
    
    def set_theme(self, theme: str):
        """Збереження теми."""
        self.set('theme', theme)
    
    def get_window_geometry(self) -> dict:
        """Отримання геометрії вікна."""
        return self.get('window', {
            'width': 900,
            'height': 700,
            'x': None,
            'y': None
        })
    
    def set_window_geometry(self, width: int, height: int, x: Optional[int] = None, y: Optional[int] = None):
        """Збереження геометрії вікна."""
        self.set('window.width', width, auto_save=False)
        self.set('window.height', height, auto_save=False)
        if x is not None:
            self.set('window.x', x, auto_save=False)
        if y is not None:
            self.set('window.y', y, auto_save=False)
        if self._config.get('auto_save_config', True):
            self.save()
    
    def get_last_output_folder(self) -> Optional[str]:
        """Отримання останньої папки збереження."""
        return self.get('last_output_folder')
    
    def set_last_output_folder(self, folder: str):
        """Збереження останньої папки збереження."""
        self.set('last_output_folder', folder)
    
    def reset_to_defaults(self):
        """Скидання конфігурації до дефолтних значень."""
        self._config = self._load_default_config()
        self.save()
        print("🔄 Конфігурацію скинуто до дефолтних значень")
