"""
Word COM Pool - Пул об'єктів MS Word для ефективної конвертації
==============================================================

Модуль для управління пулом COM об'єктів MS Word для підвищення продуктивності.
"""

import queue
import threading
import logging
from typing import Optional
from contextlib import contextmanager


class WordPool:
    """Пул COM об'єктів MS Word для повторного використання."""
    
    def __init__(self, pool_size: int = 2, timeout: float = 30.0):
        """Ініціалізація пулу.
        
        Args:
            pool_size: Максимальна кількість об'єктів Word у пулі
            timeout: Таймаут отримання об'єкта з пулу (секунди)
        """
        self.pool_size = min(pool_size, 4)  # Обмеження до 4
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self._pool: queue.Queue = queue.Queue(maxsize=self.pool_size)
        self._lock = threading.Lock()
        self._initialized = False
        self._closed = False
        
    def _create_word_instance(self) -> tuple:
        """Створення нового екземпляра Word.
        
        Returns:
            Tuple[word_app, pythoncom]: (Word Application, pythoncom модуль)
        """
        try:
            import win32com.client
            import pythoncom
            
            # Ініціалізація COM для поточного потоку
            pythoncom.CoInitialize()
            
            # Створення Word
            word = win32com.client.DispatchEx("Word.Application")
            word.Visible = False
            word.DisplayAlerts = 0
            
            self.logger.debug(f"Створено новий екземпляр Word (PID: {id(word)})")
            return (word, pythoncom)
            
        except Exception as e:
            self.logger.error(f"Не вдалося створити екземпляр Word: {e}")
            raise
    
    def initialize(self) -> None:
        """Ініціалізація пулу з попереднім створенням екземплярів."""
        if self._initialized:
            return
        
        with self._lock:
            if self._initialized:
                return
            
            self.logger.info(f"Ініціалізація пулу Word з {self.pool_size} екземпляр(ів)")
            
            # Створення початкових екземплярів
            for i in range(self.pool_size):
                try:
                    instance = self._create_word_instance()
                    self._pool.put(instance)
                    self.logger.debug(f"Додано екземпляр {i+1}/{self.pool_size} до пулу")
                except Exception as e:
                    self.logger.warning(f"Не вдалося створити екземпляр {i+1}: {e}")
                    # Продовжуємо з меншою кількістю екземплярів
                    break
            
            self._initialized = True
            self.logger.info(f"Пул Word ініціалізовано з {self._pool.qsize()} екземпляр(ів)")
    
    @contextmanager
    def get_word(self):
        """Контекстний менеджер для отримання Word з пулу.
        
        Yields:
            Word Application object
            
        Example:
            with pool.get_word() as word:
                doc = word.Documents.Open(...)
                # ... робота з документом
        """
        if self._closed:
            raise RuntimeError("Пул Word вже закрито")
        
        # Ініціалізація при першому використанні
        if not self._initialized:
            self.initialize()
        
        word_instance = None
        pythoncom_module = None
        retrieved_from_pool = False
        
        try:
            # Спроба отримати з пулу
            try:
                word_instance, pythoncom_module = self._pool.get(timeout=self.timeout)
                retrieved_from_pool = True
                self.logger.debug(f"Отримано Word з пулу (PID: {id(word_instance)}, залишилось: {self._pool.qsize()})")
            except queue.Empty:
                # Пул порожній - створюємо новий тимчасовий екземпляр
                self.logger.warning("Пул Word порожній, створюємо тимчасовий екземпляр")
                word_instance, pythoncom_module = self._create_word_instance()
                retrieved_from_pool = False
            
            # Перевірка, що Word ще живий
            try:
                _ = word_instance.Name
            except:
                self.logger.warning("Word екземпляр не відповідає, створюємо новий")
                word_instance, pythoncom_module = self._create_word_instance()
                retrieved_from_pool = False
            
            yield word_instance
            
        finally:
            # Cleanup
            if word_instance is not None:
                try:
                    # Закриваємо всі відкриті документи
                    if word_instance.Documents.Count > 0:
                        for doc in word_instance.Documents:
                            try:
                                doc.Close(SaveChanges=False)
                            except:
                                pass
                except:
                    pass
                
                # Повертаємо в пул або знищуємо
                if retrieved_from_pool and not self._closed:
                    try:
                        self._pool.put_nowait((word_instance, pythoncom_module))
                        self.logger.debug(f"Повернуто Word до пулу (PID: {id(word_instance)}, всього: {self._pool.qsize()})")
                    except queue.Full:
                        # Пул переповнений, знищуємо екземпляр
                        self._destroy_instance(word_instance, pythoncom_module)
                else:
                    # Тимчасовий екземпляр - знищуємо
                    self._destroy_instance(word_instance, pythoncom_module)
    
    def _destroy_instance(self, word_instance, pythoncom_module) -> None:
        """Знищення екземпляра Word.
        
        Args:
            word_instance: Word Application
            pythoncom_module: pythoncom модуль
        """
        try:
            word_instance.Quit()
        except:
            pass
        
        try:
            del word_instance
        except:
            pass
        
        if pythoncom_module:
            try:
                pythoncom_module.CoUninitialize()
            except:
                pass
        
        self.logger.debug("Екземпляр Word знищено")
    
    def close(self) -> None:
        """Закриття пулу та знищення всіх екземплярів."""
        if self._closed:
            return
        
        with self._lock:
            if self._closed:
                return
            
            self.logger.info("Закриття пулу Word...")
            self._closed = True
            
            # Знищення всіх екземплярів з пулу
            while not self._pool.empty():
                try:
                    word_instance, pythoncom_module = self._pool.get_nowait()
                    self._destroy_instance(word_instance, pythoncom_module)
                except queue.Empty:
                    break
                except Exception as e:
                    self.logger.error(f"Помилка при знищенні екземпляра: {e}")
            
            self.logger.info("Пул Word закрито")
    
    def __del__(self):
        """Деструктор - гарантує закриття пулу."""
        try:
            self.close()
        except:
            pass
    
    def get_stats(self) -> dict:
        """Отримати статистику пулу.
        
        Returns:
            Словник зі статистикою пулу
        """
        return {
            'pool_size': self.pool_size,
            'available': self._pool.qsize(),
            'initialized': self._initialized,
            'closed': self._closed
        }


# Глобальний singleton пулу
_global_word_pool: Optional[WordPool] = None
_pool_lock = threading.Lock()


def get_word_pool(pool_size: int = 2) -> WordPool:
    """Отримати глобальний пул Word.
    
    Args:
        pool_size: Розмір пулу (використовується тільки при першому виклику)
        
    Returns:
        WordPool instance
    """
    global _global_word_pool
    
    if _global_word_pool is None:
        with _pool_lock:
            if _global_word_pool is None:
                _global_word_pool = WordPool(pool_size=pool_size)
    
    return _global_word_pool


def close_global_pool() -> None:
    """Закрити глобальний пул Word."""
    global _global_word_pool
    
    if _global_word_pool is not None:
        with _pool_lock:
            if _global_word_pool is not None:
                _global_word_pool.close()
                _global_word_pool = None
