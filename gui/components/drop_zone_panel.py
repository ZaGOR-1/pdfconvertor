"""
Drop Zone Panel - Drag & Drop область
====================================

Компонент для перетягування файлів та папок.
"""

import customtkinter as ctk
from pathlib import Path
from tkinterdnd2 import DND_FILES
from typing import Callable, Optional
import re


class DropZonePanel(ctk.CTkFrame):
    """Панель для drag & drop файлів."""
    
    def __init__(
        self, 
        parent, 
        on_files_dropped: Callable[[list], None],
        on_click: Callable,
        theme_manager,
        i18n,
        **kwargs
    ):
        """Ініціалізація drop zone панелі.
        
        Args:
            parent: Батьківський віджет
            on_files_dropped: Callback для обробки файлів
            on_click: Callback для кліку на область
            theme_manager: Менеджер тем
            i18n: Система локалізації
        """
        super().__init__(parent, **kwargs)
        
        self.on_files_dropped = on_files_dropped
        self.on_click = on_click
        self.theme_manager = theme_manager
        self.i18n = i18n
        
        self._create_ui()
        self._setup_drag_and_drop()
    
    def _create_ui(self):
        """Створення UI елементів."""
        # Drag & Drop область з анімованою рамкою
        self.drop_area = ctk.CTkFrame(
            self,
            corner_radius=15,
            border_width=3,
            border_color=self.theme_manager.get_color("drop_zone_border"),
            fg_color=self.theme_manager.get_color("drop_zone_bg")
        )
        self.drop_area.grid(row=0, column=0, sticky="nsew", padx=20, pady=10)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Контейнер для контенту (для центрування)
        drop_content = ctk.CTkFrame(self.drop_area, fg_color="transparent")
        drop_content.place(relx=0.5, rely=0.5, anchor="center")
        
        # Робимо область кліком
        self.drop_area.bind('<Button-1>', self.on_click)
        self.drop_area.configure(cursor="hand2")
        
        # Додаємо клік на контент також
        drop_content.bind('<Button-1>', self.on_click)
        drop_content.configure(cursor="hand2")
        
        # Іконка
        self.drop_icon_label = ctk.CTkLabel(
            drop_content,
            text=self.i18n.get("icon_clip"),
            font=ctk.CTkFont(size=48),
            cursor="hand2"
        )
        self.drop_icon_label.pack(pady=(20, 10))
        self.drop_icon_label.bind('<Button-1>', self.on_click)
        
        # Основний текст
        drop_text_main = ctk.CTkLabel(
            drop_content,
            text=self.i18n.get("drop_zone_title"),
            font=ctk.CTkFont(size=16, weight="bold"),
            cursor="hand2"
        )
        drop_text_main.pack(pady=(0, 5))
        drop_text_main.bind('<Button-1>', self.on_click)
        
        # Допоміжний текст
        drop_text_help = ctk.CTkLabel(
            drop_content,
            text=self.i18n.get("drop_zone_subtitle"),
            font=ctk.CTkFont(size=12),
            text_color=self.theme_manager.get_color("text_secondary"),
            cursor="hand2"
        )
        drop_text_help.pack(pady=(0, 10))
        drop_text_help.bind('<Button-1>', self.on_click)
        
        # Підтримувані формати
        formats_label = ctk.CTkLabel(
            drop_content,
            text=self.i18n.get("drop_zone_formats"),
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60"),
            cursor="hand2"
        )
        formats_label.pack(pady=(0, 20))
        formats_label.bind('<Button-1>', self.on_click)
    
    def _setup_drag_and_drop(self):
        """Налаштування drag & drop функціоналу."""
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self._on_drop)
        self.drop_area.dnd_bind('<<DragEnter>>', self._on_drag_enter)
        self.drop_area.dnd_bind('<<DragLeave>>', self._on_drag_leave)
    
    def _on_drop(self, event):
        """Обробник події drop."""
        files_str = event.data
        
        # Парсинг шляхів
        pattern = r'\{([^}]+)\}|(\S+)'
        matches = re.findall(pattern, files_str)
        files = [match[0] if match[0] else match[1] for match in matches]
        
        # Конвертація у Path об'єкти
        paths = []
        for f in files:
            clean_path = f.strip().strip('{}').strip('"').strip("'")
            paths.append(Path(clean_path).resolve())
        
        # Виклик callback
        self.on_files_dropped(paths)
        
        # Повернення до нормального вигляду
        self.drop_area.configure(border_color=self.theme_manager.get_color("drop_zone_border"))
        self.drop_icon_label.configure(text=self.i18n.get("icon_clip"))
    
    def _on_drag_enter(self, event):
        """Обробник наведення файлів."""
        self.drop_area.configure(border_color=self.theme_manager.get_color("accent_hover"))
        self.drop_icon_label.configure(text=self.i18n.get("icon_download"))
    
    def _on_drag_leave(self, event):
        """Обробник виходу курсора."""
        self.drop_area.configure(border_color=self.theme_manager.get_color("drop_zone_border"))
        self.drop_icon_label.configure(text=self.i18n.get("icon_clip"))
