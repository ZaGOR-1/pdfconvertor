"""
File Handler - Робота з файлами та валідація
===========================================

Модуль для валідації файлів, отримання метаданих та роботи з шляхами.
"""

from pathlib import Path
from typing import Optional, Tuple, List, Dict
import os
import zipfile
import shutil
import time
from functools import lru_cache


class FileHandler:
    """Клас для роботи з файлами."""
    
    SUPPORTED_EXTENSIONS = {'.doc', '.docx'}
    MAX_FILE_SIZE_MB = 100
    CACHE_TTL_SECONDS = 300  # 5 хвилин
    CACHE_MAX_SIZE = 1000
    
    # Кеш для результатів валідації з TTL
    _validation_cache: Dict[str, Tuple[bool, str, float]] = {}
    
    @classmethod
    def set_max_file_size(cls, size_mb: int):
        """Встановити максимальний розмір файлу.
        
        Args:
            size_mb: Максимальний розмір в МБ
        """
        cls.MAX_FILE_SIZE_MB = max(1, min(size_mb, 500))  # Обмеження 1-500 МБ
    
    @staticmethod
    def is_word_file(file_path: Path) -> bool:
        """Перевірка, чи є файл Word документом.
        
        Args:
            file_path: Шлях до файлу
            
        Returns:
            True, якщо файл має підтримуване розширення
        """
        return file_path.suffix.lower() in FileHandler.SUPPORTED_EXTENSIONS
    
    @staticmethod
    def check_disk_space(directory: Path, required_mb: float = 10) -> Tuple[bool, str]:
        """Перевірка вільного місця на диску.
        
        Args:
            directory: Шлях до директорії
            required_mb: Необхідна кількість вільного місця в MB
            
        Returns:
            Tuple[bool, str]: (достатньо місця, повідомлення)
        """
        try:
            # Отримання інформації про диск
            stat = shutil.disk_usage(directory)
            free_mb = stat.free / (1024 * 1024)
            
            if free_mb < required_mb:
                return False, f"Недостатньо місця на диску: {free_mb:.1f} MB (потрібно {required_mb} MB)"
            
            return True, f"Вільно: {free_mb:.1f} MB"
            
        except Exception as e:
            return False, f"Помилка перевірки диску: {str(e)}"
    
    @staticmethod
    def estimate_pdf_size(word_file: Path) -> float:
        """Оцінка розміру PDF файлу в MB.
        
        Args:
            word_file: Шлях до Word файлу
            
        Returns:
            Оцінка розміру PDF в MB
        """
        try:
            # PDF зазвичай трохи більший за DOCX (коефіцієнт 1.2-1.5)
            word_size_mb = word_file.stat().st_size / (1024 * 1024)
            return word_size_mb * 1.3
        except:
            return 10  # За замовчуванням 10 MB
    
    @staticmethod
    def validate_file(file_path: Path, use_cache: bool = True) -> Tuple[bool, str]:
        """Валідація файлу перед конвертацією з кешуванням.
        
        Args:
            file_path: Шлях до файлу
            use_cache: Використовувати кеш
            
        Returns:
            Tuple[bool, str]: (валідний, повідомлення про помилку)
        """
        # Перевірка кешу (ключ: шлях + mtime)
        if use_cache:
            try:
                mtime = file_path.stat().st_mtime
                cache_key = f"{file_path}_{mtime}"
                
                if cache_key in FileHandler._validation_cache:
                    cached_valid, cached_msg, cached_time = FileHandler._validation_cache[cache_key]
                    # Перевірка TTL
                    if time.time() - cached_time < FileHandler.CACHE_TTL_SECONDS:
                        return cached_valid, cached_msg
                    else:
                        # Видалення застарілого запису
                        del FileHandler._validation_cache[cache_key]
            except:
                pass
        
        # Перевірка існування
        if not file_path.exists():
            return False, f"Файл не існує: {file_path}"
        
        # Перевірка, що це файл, а не директорія
        if not file_path.is_file():
            return False, f"Це не файл: {file_path}"
        
        # Перевірка розширення
        if not FileHandler.is_word_file(file_path):
            return False, f"Непідтримуване розширення: {file_path.suffix}"
        
        # Перевірка розміру
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > FileHandler.MAX_FILE_SIZE_MB:
            return False, f"Файл занадто великий: {size_mb:.1f} MB (максимум {FileHandler.MAX_FILE_SIZE_MB} MB)"
        
        # Перевірка доступу до читання
        if not os.access(file_path, os.R_OK):
            return False, f"Немає доступу до читання: {file_path}"
        
        # Перевірка цілісності файлу (тільки якщо не в кеші)
        is_valid, error = FileHandler.check_file_integrity(file_path)
        if not is_valid:
            result = (False, error)
        else:
            result = (True, "OK")
        
        # Збереження в кеш
        if use_cache:
            try:
                mtime = file_path.stat().st_mtime
                cache_key = f"{file_path}_{mtime}"
                FileHandler._validation_cache[cache_key] = (result[0], result[1], time.time())
                
                # Очищення застарілих та обмеження розміру кешу
                if len(FileHandler._validation_cache) > FileHandler.CACHE_MAX_SIZE:
                    current_time = time.time()
                    # Видалення записів старших за TTL
                    expired_keys = [
                        k for k, v in FileHandler._validation_cache.items()
                        if current_time - v[2] > FileHandler.CACHE_TTL_SECONDS
                    ]
                    for key in expired_keys:
                        del FileHandler._validation_cache[key]
                    
                    # Якщо ще багато - видалити найстаріші
                    if len(FileHandler._validation_cache) > FileHandler.CACHE_MAX_SIZE:
                        oldest_keys = sorted(
                            FileHandler._validation_cache.keys(),
                            key=lambda k: FileHandler._validation_cache[k][2]
                        )[:FileHandler.CACHE_MAX_SIZE // 2]
                        for key in oldest_keys:
                            del FileHandler._validation_cache[key]
            except:
                pass
        
        return result
    
    @staticmethod
    def check_file_integrity(file_path: Path) -> Tuple[bool, str]:
        """Перевірка цілісності Word документа.
        
        Args:
            file_path: Шлях до файлу
            
        Returns:
            Tuple[bool, str]: (валідний, повідомлення про помилку)
        """
        try:
            # DOCX - це ZIP архів
            if file_path.suffix.lower() == '.docx':
                if not zipfile.is_zipfile(file_path):
                    return False, f"Файл пошкоджений: {file_path.name}"
                
                # Перевіряємо структуру DOCX
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Обов'язкові файли в DOCX
                    required_files = ['[Content_Types].xml', 'word/document.xml']
                    zip_files = zip_ref.namelist()
                    
                    for required in required_files:
                        if required not in zip_files:
                            return False, f"Файл пошкоджений (відсутній {required}): {file_path.name}"
                    
                    # Перевіряємо, що можна прочитати document.xml
                    try:
                        zip_ref.read('word/document.xml')
                    except Exception:
                        return False, f"Файл пошкоджений (не можна прочитати вміст): {file_path.name}"
            
            # DOC - перевіряємо магічну сигнатуру
            elif file_path.suffix.lower() == '.doc':
                with open(file_path, 'rb') as f:
                    header = f.read(8)
                    # DOC файли починаються з D0 CF 11 E0 A1 B1 1A E1 (OLE2)
                    if len(header) < 8 or header[:8] != b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1':
                        return False, f"Файл пошкоджений або не є DOC: {file_path.name}"
            
            return True, "OK"
            
        except zipfile.BadZipFile:
            return False, f"Файл пошкоджений (невалідний ZIP): {file_path.name}"
        except PermissionError:
            return False, f"Немає доступу до файлу: {file_path.name}"
        except Exception as e:
            return False, f"Помилка перевірки файлу: {str(e)}"
    
    @staticmethod
    def get_word_files_from_directory(directory: Path, recursive: bool = True) -> List[Path]:
        """Пошук всіх Word файлів у директорії.
        
        Args:
            directory: Шлях до директорії
            recursive: Рекурсивний пошук у піддиректоріях
            
        Returns:
            Список шляхів до Word файлів
        """
        word_files = []
        
        try:
            if not directory.exists() or not directory.is_dir():
                return word_files
            
            # Рекурсивний пошук
            if recursive:
                for ext in FileHandler.SUPPORTED_EXTENSIONS:
                    word_files.extend(directory.rglob(f'*{ext}'))
            else:
                for ext in FileHandler.SUPPORTED_EXTENSIONS:
                    word_files.extend(directory.glob(f'*{ext}'))
            
            return sorted(word_files)
            
        except Exception as e:
            print(f"Помилка пошуку файлів: {e}")
            return []
    
    @staticmethod
    def get_file_size(file_path: Path) -> str:
        """Отримання розміру файлу у читабельному форматі.
        
        Args:
            file_path: Шлях до файлу
            
        Returns:
            Рядок з розміром (наприклад, "1.5 MB" або "250 KB")
        """
        try:
            size_bytes = file_path.stat().st_size
            
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.0f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.2f} MB"
        except Exception:
            return "N/A"
    
    @staticmethod
    def get_output_path(
        input_path: Path,
        output_dir: Optional[Path] = None,
        auto_number: bool = False
    ) -> Path:
        """Генерація шляху для вихідного PDF файлу.
        
        Args:
            input_path: Шлях до вхідного файлу
            output_dir: Директорія для збереження (опціонально)
            auto_number: Автоматична нумерація при дублікатах
            
        Returns:
            Шлях до вихідного PDF файлу
        """
        pdf_name = input_path.with_suffix('.pdf').name
        
        if output_dir:
            output_path = output_dir / pdf_name
        else:
            output_path = input_path.with_suffix('.pdf')
        
        # Автоматична нумерація при дублікатах
        if auto_number and output_path.exists():
            base_name = output_path.stem
            extension = output_path.suffix
            parent_dir = output_path.parent
            counter = 1
            
            while output_path.exists():
                new_name = f"{base_name} ({counter}){extension}"
                output_path = parent_dir / new_name
                counter += 1
        
        return output_path
    
    @staticmethod
    def check_output_exists(output_path: Path) -> bool:
        """Перевірка, чи існує вихідний PDF файл.
        
        Args:
            output_path: Шлях до PDF файлу
            
        Returns:
            True, якщо файл вже існує
        """
        return output_path.exists()
    
    @staticmethod
    def ensure_directory(directory: Path) -> bool:
        """Створення директорії, якщо вона не існує.
        
        Args:
            directory: Шлях до директорії
            
        Returns:
            True, якщо директорія існує або успішно створена
        """
        try:
            directory.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_unique_filename(file_path: Path) -> Path:
        """Генерація унікального імені файлу, якщо файл вже існує.
        
        Args:
            file_path: Бажаний шлях до файлу
            
        Returns:
            Унікальний шлях (з доданням (1), (2) тощо, якщо потрібно)
        """
        if not file_path.exists():
            return file_path
        
        # Розділення на ім'я та розширення
        stem = file_path.stem
        suffix = file_path.suffix
        parent = file_path.parent
        
        # Пошук унікального імені
        counter = 1
        while True:
            new_name = f"{stem} ({counter}){suffix}"
            new_path = parent / new_name
            
            if not new_path.exists():
                return new_path
            
            counter += 1
            
            # Захист від нескінченного циклу
            if counter > 1000:
                return file_path


# Тестування
if __name__ == "__main__":
    print("FileHandler - Тестування")
    print("=" * 50)
    
    # Тест валідації розширень
    test_files = [
        Path("test.docx"),
        Path("test.doc"),
        Path("test.pdf"),
        Path("test.txt")
    ]
    
    for file in test_files:
        is_word = FileHandler.is_word_file(file)
        print(f"{file.name}: {'✅' if is_word else '❌'} Word файл")
    
    print("\nМаксимальний розмір:", FileHandler.MAX_FILE_SIZE_MB, "MB")
