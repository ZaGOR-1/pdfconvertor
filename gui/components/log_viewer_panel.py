"""
Log Viewer Panel - Панель для перегляду логів
============================================

Компонент для відображення логів в реальному часі.
"""

import customtkinter as ctk
from typing import Optional
import threading
import queue


class LogViewerPanel(ctk.CTkToplevel):
    """Вікно для перегляду логів в реальному часі."""
    
    def __init__(self, parent, theme_manager):
        """Ініціалізація панелі логів.
        
        Args:
            parent: Батьківське вікно
            theme_manager: Менеджер тем
        """
        super().__init__(parent)
        
        self.theme_manager = theme_manager
        self.log_queue = queue.Queue()
        self.is_running = True
        
        # Налаштування вікна
        self.title("📋 Логи конвертації")
        self.geometry("700x500")
        self.minsize(600, 400)
        
        # Встановлення вікна поверх основного
        self.transient(parent)
        self.lift()
        self.focus_force()
        
        # Центрування
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.winfo_screenheight() // 2) - (500 // 2)
        self.geometry(f"700x500+{x}+{y}")
        
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self._create_ui()
        self._start_log_updater()
    
    def _create_ui(self):
        """Створення UI елементів."""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="📋 Логи конвертації",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(side="left")
        
        # Кнопки управління
        btn_clear = ctk.CTkButton(
            header_frame,
            text="Очистити",
            width=100,
            command=self._clear_logs
        )
        btn_clear.pack(side="right", padx=5)
        
        btn_copy = ctk.CTkButton(
            header_frame,
            text="Копіювати",
            width=100,
            command=self._copy_logs
        )
        btn_copy.pack(side="right")
        
        # Текстове поле для логів
        self.log_text = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def add_log(self, message: str, level: str = "INFO"):
        """Додати лог повідомлення.
        
        Args:
            message: Текст повідомлення
            level: Рівень логування (INFO, WARNING, ERROR)
        """
        self.log_queue.put((message, level))
    
    def _start_log_updater(self):
        """Запуск оновлювача логів."""
        def update_loop():
            while self.is_running:
                try:
                    message, level = self.log_queue.get(timeout=0.1)
                    self.after(0, lambda m=message, l=level: self._append_log(m, l))
                except queue.Empty:
                    continue
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
    
    def _append_log(self, message: str, level: str):
        """Додати повідомлення в текстове поле."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Іконки для рівнів
        icons = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "SUCCESS": "✅"
        }
        icon = icons.get(level, "•")
        
        log_line = f"[{timestamp}] {icon} {message}\n"
        
        self.log_text.insert("end", log_line)
        self.log_text.see("end")  # Прокрутка вниз
    
    def _clear_logs(self):
        """Очистити логи."""
        self.log_text.delete("1.0", "end")
    
    def _copy_logs(self):
        """Копіювати логи в буфер обміну."""
        logs = self.log_text.get("1.0", "end")
        self.clipboard_clear()
        self.clipboard_append(logs)
        self.add_log("Логи скопійовано в буфер обміну", "SUCCESS")
    
    def _on_closing(self):
        """Закриття вікна."""
        self.is_running = False
        self.destroy()
