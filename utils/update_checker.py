"""
Update Checker - Перевірка оновлень програми
===========================================

Модуль для перевірки доступності нових версій програми.
"""

import requests
import logging
from typing import Tuple, Optional
from packaging import version
import json


class UpdateChecker:
    """Клас для перевірки оновлень програми."""
    
    CURRENT_VERSION = "0.1.0"
    UPDATE_URL = "https://api.github.com/repos/user/word-to-pdf-converter/releases/latest"
    TIMEOUT = 5  # секунд
    
    def __init__(self):
        """Ініціалізація перевірки оновлень."""
        self.logger = logging.getLogger(__name__)
    
    def check_for_updates(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Перевірка наявності нових версій.
        
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: 
                (є_оновлення, нова_версія, url_завантаження)
        """
        try:
            self.logger.info(f"Перевірка оновлень. Поточна версія: {self.CURRENT_VERSION}")
            
            # Запит до API з обробкою помилок мережі
            response = requests.get(
                self.UPDATE_URL, 
                timeout=self.TIMEOUT,
                headers={'Accept': 'application/vnd.github.v3+json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get('tag_name', '').lstrip('v')
                download_url = data.get('html_url', '')
                
                self.logger.info(f"Остання версія на сервері: {latest_version}")
                
                # Порівняння версій
                if self._is_newer_version(latest_version):
                    self.logger.info(f"✅ Доступна нова версія: {latest_version}")
                    return True, latest_version, download_url
                else:
                    self.logger.info("✅ Використовується остання версія")
                    return False, latest_version, None
            else:
                self.logger.warning(f"Не вдалося перевірити оновлення: HTTP {response.status_code}")
                return False, None, None
                
        except requests.Timeout:
            self.logger.warning(f"Тайм-аут при перевірці оновлень ({self.TIMEOUT}s)")
            return False, None, None
        except requests.ConnectionError as e:
            self.logger.warning(f"Помилка підключення до сервера оновлень: {e}")
            return False, None, None
        except requests.RequestException as e:
            self.logger.warning(f"Помилка HTTP при перевірці оновлень: {e}")
            return False, None, None
        except Exception as e:
            self.logger.error(f"Неочікувана помилка при перевірці оновлень: {e}")
            return False, None, None
    
    def _is_newer_version(self, remote_version: str) -> bool:
        """Порівняння версій.
        
        Args:
            remote_version: Версія на сервері
            
        Returns:
            True якщо віддалена версія новіша
        """
        try:
            current = version.parse(self.CURRENT_VERSION)
            remote = version.parse(remote_version)
            return remote > current
        except Exception as e:
            self.logger.error(f"Помилка порівняння версій: {e}")
            return False
    
    def check_for_updates_async(self, callback):
        """Асинхронна перевірка оновлень.
        
        Args:
            callback: Функція зворотного виклику (has_update, version, url)
        """
        import threading
        
        def check():
            result = self.check_for_updates()
            callback(*result)
        
        thread = threading.Thread(target=check, daemon=True)
        thread.start()
    
    @staticmethod
    def get_current_version() -> str:
        """Отримання поточної версії програми.
        
        Returns:
            Рядок з версією
        """
        return UpdateChecker.CURRENT_VERSION


# Тестування
if __name__ == "__main__":
    print("Update Checker - Тестування")
    print("=" * 50)
    
    checker = UpdateChecker()
    has_update, new_version, url = checker.check_for_updates()
    
    print(f"Поточна версія: {checker.CURRENT_VERSION}")
    print(f"Є оновлення: {has_update}")
    if has_update:
        print(f"Нова версія: {new_version}")
        print(f"URL: {url}")
