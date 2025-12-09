"""
Recovery Manager - Механізм відновлення конвертації
=================================================

Модуль для збереження та відновлення стану конвертації.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class RecoveryManager:
    """Клас для управління відновленням конвертації."""
    
    RECOVERY_FILE = "recovery.json"
    
    def __init__(self, recovery_dir: Optional[Path] = None):
        """Ініціалізація менеджера відновлення.
        
        Args:
            recovery_dir: Директорія для збереження файлу відновлення
        """
        self.logger = logging.getLogger(__name__)
        
        if recovery_dir is None:
            recovery_dir = Path(__file__).parent.parent / "logs"
        
        self.recovery_dir = Path(recovery_dir)
        self.recovery_dir.mkdir(parents=True, exist_ok=True)
        self.recovery_file = self.recovery_dir / self.RECOVERY_FILE
    
    def save_state(self, files: List[Path], output_folder: Optional[Path], 
                   processed: List[int], failed: List[int]) -> bool:
        """Збереження стану конвертації.
        
        Args:
            files: Список файлів для конвертації
            output_folder: Папка для збереження PDF
            processed: Індекси успішно оброблених файлів
            failed: Індекси файлів з помилками
            
        Returns:
            True якщо збереження успішне
        """
        try:
            state = {
                "timestamp": datetime.now().isoformat(),
                "files": [str(f) for f in files],
                "output_folder": str(output_folder) if output_folder else None,
                "processed": processed,
                "failed": failed,
                "total": len(files),
                "remaining": len(files) - len(processed) - len(failed)
            }
            
            with open(self.recovery_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"💾 Стан конвертації збережено: {len(processed)} оброблено, "
                           f"{len(failed)} помилок, {state['remaining']} залишилось")
            return True
            
        except Exception as e:
            self.logger.error(f"Помилка збереження стану: {e}")
            return False
    
    def load_state(self) -> Optional[Dict[str, Any]]:
        """Завантаження збереженого стану конвертації.
        
        Returns:
            Словник зі станом або None якщо файл не існує
        """
        try:
            if not self.recovery_file.exists():
                return None
            
            with open(self.recovery_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            self.logger.info(f"📂 Знайдено збережений стан: {state['remaining']} файлів залишилось")
            return state
            
        except Exception as e:
            self.logger.error(f"Помилка завантаження стану: {e}")
            return None
    
    def clear_state(self) -> bool:
        """Видалення файлу відновлення.
        
        Returns:
            True якщо видалення успішне
        """
        try:
            if self.recovery_file.exists():
                self.recovery_file.unlink()
                self.logger.info("🗑️ Файл відновлення видалено")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Помилка видалення файлу відновлення: {e}")
            return False
    
    def has_recovery_data(self) -> bool:
        """Перевірка наявності даних для відновлення.
        
        Returns:
            True якщо є збережений стан
        """
        return self.recovery_file.exists()
    
    def get_recovery_info(self) -> Optional[str]:
        """Отримання інформації про збережений стан.
        
        Returns:
            Рядок з інформацією або None
        """
        state = self.load_state()
        if not state:
            return None
        
        try:
            timestamp = datetime.fromisoformat(state['timestamp'])
            time_str = timestamp.strftime("%d.%m.%Y %H:%M")
            
            info = (
                f"Знайдено незавершену конвертацію від {time_str}\n\n"
                f"📊 Всього файлів: {state['total']}\n"
                f"✅ Оброблено: {len(state['processed'])}\n"
                f"❌ Помилок: {len(state['failed'])}\n"
                f"⏳ Залишилось: {state['remaining']}\n\n"
                f"Продовжити конвертацію?"
            )
            return info
            
        except Exception as e:
            self.logger.error(f"Помилка формування інформації: {e}")
            return None
    
    def get_remaining_files(self) -> Optional[List[Path]]:
        """Отримання списку файлів, які ще не оброблені.
        
        Returns:
            Список файлів або None
        """
        state = self.load_state()
        if not state:
            return None
        
        try:
            all_files = [Path(f) for f in state['files']]
            processed_indices = set(state['processed'] + state['failed'])
            
            remaining = [f for i, f in enumerate(all_files) if i not in processed_indices]
            
            self.logger.info(f"📋 Знайдено {len(remaining)} необроблених файлів")
            return remaining
            
        except Exception as e:
            self.logger.error(f"Помилка отримання файлів: {e}")
            return None


# Тестування
if __name__ == "__main__":
    print("Recovery Manager - Тестування")
    print("=" * 50)
    
    recovery = RecoveryManager()
    
    # Тест збереження
    test_files = [Path("file1.docx"), Path("file2.docx"), Path("file3.docx")]
    success = recovery.save_state(test_files, Path("output"), [0], [1])
    print(f"Збереження: {'✅' if success else '❌'}")
    
    # Тест завантаження
    state = recovery.load_state()
    print(f"Завантаження: {'✅' if state else '❌'}")
    
    if state:
        print(f"Залишилось файлів: {state['remaining']}")
    
    # Тест інформації
    info = recovery.get_recovery_info()
    if info:
        print("\nІнформація про відновлення:")
        print(info)
    
    # Тест очищення
    clear_success = recovery.clear_state()
    print(f"\nОчищення: {'✅' if clear_success else '❌'}")
