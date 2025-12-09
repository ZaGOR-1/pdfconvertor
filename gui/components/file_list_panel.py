"""
File List Panel - Панель зі списком файлів
=========================================

Компонент для відображення та управління списком файлів.
"""

import customtkinter as ctk
from pathlib import Path
from typing import List, Callable, Dict, Optional
from converter.file_handler import FileHandler


class FileListPanel(ctk.CTkFrame):
    """Панель зі списком файлів для конвертації."""
    
    def __init__(
        self,
        parent,
        on_remove_file: Callable[[Path, int], None],
        theme_manager,
        i18n,
        **kwargs
    ):
        """Ініціалізація панелі списку файлів.
        
        Args:
            parent: Батьківський віджет
            on_remove_file: Callback для видалення файлу
            theme_manager: Менеджер тем
            i18n: Система локалізації
        """
        super().__init__(parent, **kwargs)
        
        self.on_remove_file = on_remove_file
        self.theme_manager = theme_manager
        self.i18n = i18n
        
        self.file_widgets: List[ctk.CTkFrame] = []
        self.file_progress_bars: Dict[int, ctk.CTkProgressBar] = {}
        
        self._create_ui()
    
    def _create_ui(self):
        """Створення UI елементів."""
        # Заголовок
        header = ctk.CTkLabel(
            self,
            text="📋 Список файлів",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        header.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        # Scrollable контейнер для файлів
        self.files_scroll = ctk.CTkScrollableFrame(
            self,
            height=300,
            fg_color="transparent"
        )
        self.files_scroll.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.files_scroll.grid_columnconfigure(0, weight=1)
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def add_file(self, file_path: Path, file_index: int):
        """Додати файл до списку.
        
        Args:
            file_path: Шлях до файлу
            file_index: Індекс файлу в списку
        """
        # Контейнер для файлу
        file_frame = ctk.CTkFrame(
            self.files_scroll,
            corner_radius=8,
            fg_color=self.theme_manager.get_color("bg_secondary")
        )
        file_frame.grid(sticky="ew", padx=5, pady=3)
        file_frame.grid_columnconfigure(1, weight=1)
        
        # Іконка файлу
        icon_label = ctk.CTkLabel(
            file_frame,
            text=self.i18n.get("icon_document"),
            font=ctk.CTkFont(size=20),
            width=40
        )
        icon_label.grid(row=0, column=0, padx=(10, 5), pady=10, rowspan=2)
        
        # Ім'я файлу
        name_label = ctk.CTkLabel(
            file_frame,
            text=file_path.name,
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        name_label.grid(row=0, column=1, sticky="w", padx=5, pady=(10, 0))
        
        # Розмір файлу
        size_text = FileHandler.get_file_size(file_path)
        size_label = ctk.CTkLabel(
            file_frame,
            text=size_text,
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
            width=80
        )
        size_label.grid(row=0, column=2, padx=5, pady=10, rowspan=2)
        
        # Статус
        status_label = ctk.CTkLabel(
            file_widget,
            text=self.i18n.get("file_waiting"),
            font=ctk.CTkFont(size=11),
            text_color=self.theme_manager.get_color("text_secondary"),
            width=120
        )
        status_label.grid(row=0, column=3, padx=5, pady=10, rowspan=2)
        
        # Прогрес бар (спочатку схований)
        progress_bar = ctk.CTkProgressBar(
            file_frame,
            mode="indeterminate",
            width=100,
            height=15
        )
        progress_bar.grid(row=1, column=1, sticky="ew", padx=5, pady=(0, 10))
        progress_bar.grid_remove()
        self.file_progress_bars[file_index] = progress_bar
        
        # Кнопка видалення
        delete_btn = ctk.CTkButton(
            file_frame,
            text="✕",
            width=30,
            height=30,
            fg_color=self.theme_manager.get_color("error"),
            hover_color=self.theme_manager.get_color("error"),
            command=lambda: self.on_remove_file(file_path, file_frame, file_index)
        )
        delete_btn.grid(row=0, column=4, padx=10, pady=10, rowspan=2)
        
        # Зберігаємо посилання на віджет
        self.file_widgets.append(file_frame)
        
        # Зберігаємо label статусу для подальшого оновлення
        file_frame.status_label = status_label
    
    def clear_all(self):
        """Очистити всі файли зі списку."""
        for widget in self.file_widgets:
            widget.destroy()
        
        self.file_widgets.clear()
        self.file_progress_bars.clear()
    
    def remove_file(self, widget: ctk.CTkFrame, file_index: int):
        """Видалити файл зі списку.
        
        Args:
            widget: Віджет файлу
            file_index: Індекс файлу
        """
        if widget in self.file_widgets:
            self.file_widgets.remove(widget)
        
        if file_index in self.file_progress_bars:
            del self.file_progress_bars[file_index]
        
        widget.destroy()
    
    def show_progress(self, file_index: int):
        """Показати прогрес бар для файлу.
        
        Args:
            file_index: Індекс файлу
        """
        if file_index in self.file_progress_bars:
            progress_bar = self.file_progress_bars[file_index]
            progress_bar.grid()
            progress_bar.start()
    
    def hide_progress(self, file_index: int):
        """Сховати прогрес бар файлу.
        
        Args:
            file_index: Індекс файлу
        """
        if file_index in self.file_progress_bars:
            progress_bar = self.file_progress_bars[file_index]
            progress_bar.stop()
            progress_bar.grid_remove()
    
    def update_status(self, file_index: int, status: str):
        """Оновити статус файлу.
        
        Args:
            file_index: Індекс файлу
            status: Новий статус
        """
        if file_index < len(self.file_widgets):
            widget = self.file_widgets[file_index]
            if hasattr(widget, 'status_label'):
                widget.status_label.configure(text=status)
    
    def get_file_count(self) -> int:
        """Отримати кількість файлів у списку."""
        return len(self.file_widgets)
