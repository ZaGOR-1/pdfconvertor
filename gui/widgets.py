"""
Кастомні віджети для Word to PDF Converter.
Містить розширені UI компоненти з анімаціями та ефектами.
"""

from typing import Optional, Callable
import customtkinter as ctk
from pathlib import Path


class AnimatedButton(ctk.CTkButton):
    """Кнопка з анімованими hover ефектами."""
    
    def __init__(self, master, hover_color: Optional[str] = None, 
                 default_color: Optional[str] = None, **kwargs):
        """
        Ініціалізація анімованої кнопки.
        
        Args:
            master: Батьківський віджет
            hover_color: Колір при наведенні
            default_color: Стандартний колір
            **kwargs: Додаткові параметри для CTkButton
        """
        super().__init__(master, **kwargs)
        
        self.default_color = default_color or self.cget("fg_color")
        self.hover_color = hover_color or self._calculate_hover_color()
        
        # Прив'язка подій
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _calculate_hover_color(self) -> str:
        """Автоматичний розрахунок кольору при наведенні."""
        # Для спрощення повертаємо світліший відтінок
        return "#3e8bc7"
    
    def _on_enter(self, event):
        """Обробка наведення миші."""
        self.configure(fg_color=self.hover_color)
    
    def _on_leave(self, event):
        """Обробка виходу миші."""
        self.configure(fg_color=self.default_color)


class FileItemWidget(ctk.CTkFrame):
    """Віджет для відображення окремого файлу у списку."""
    
    def __init__(self, master, file_path: Path, on_remove: Optional[Callable] = None, **kwargs):
        """
        Ініціалізація віджета файлу.
        
        Args:
            master: Батьківський віджет
            file_path: Шлях до файлу
            on_remove: Callback при видаленні файлу
            **kwargs: Додаткові параметри
        """
        super().__init__(master, **kwargs)
        
        self.file_path = file_path
        self.on_remove = on_remove
        
        # Налаштування сітки
        self.grid_columnconfigure(1, weight=1)
        
        # Іконка файлу
        icon_label = ctk.CTkLabel(
            self,
            text="📄",
            font=ctk.CTkFont(size=20),
            width=30
        )
        icon_label.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")
        
        # Інформація про файл
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Назва файлу
        file_name = ctk.CTkLabel(
            info_frame,
            text=file_path.name,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        file_name.pack(anchor="w")
        
        # Розмір файлу
        file_size = self._format_file_size(file_path)
        size_label = ctk.CTkLabel(
            info_frame,
            text=file_size,
            font=ctk.CTkFont(size=10),
            text_color=("#6c757d", "gray60"),
            anchor="w"
        )
        size_label.pack(anchor="w")
        
        # Статус
        self.status_label = ctk.CTkLabel(
            self,
            text="⏳ Очікує",
            font=ctk.CTkFont(size=11),
            width=100
        )
        self.status_label.grid(row=0, column=2, padx=5, pady=10)
        
        # Прогрес бар
        self.progress_bar = ctk.CTkProgressBar(
            self,
            width=100,
            height=10
        )
        self.progress_bar.grid(row=0, column=3, padx=5, pady=10)
        self.progress_bar.set(0)
        
        # Кнопка видалення
        if on_remove:
            remove_btn = ctk.CTkButton(
                self,
                text="✕",
                width=30,
                height=30,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="transparent",
                text_color=("#dc3545", "#ff4444"),
                hover_color=("#f8d7da", "#8b0000"),
                command=lambda: on_remove(file_path)
            )
            remove_btn.grid(row=0, column=4, padx=(5, 10), pady=10)
        
        # Hover ефект
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _format_file_size(self, file_path: Path) -> str:
        """Форматування розміру файлу."""
        try:
            size_bytes = file_path.stat().st_size
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
        except:
            return "N/A"
    
    def _on_enter(self, event):
        """Hover ефект - затемнення фону."""
        self.configure(fg_color=("#e9ecef", "#3b3b3b"))
    
    def _on_leave(self, event):
        """Повернення до нормального фону."""
        self.configure(fg_color=("#f8f9fa", "#2b2b2b"))
    
    def set_status(self, status: str, color: Optional[str] = None):
        """
        Встановлення статусу файлу.
        
        Args:
            status: Текст статусу
            color: Колір тексту статусу
        """
        self.status_label.configure(text=status)
        if color:
            self.status_label.configure(text_color=color)
    
    def set_progress(self, value: float):
        """
        Встановлення прогресу.
        
        Args:
            value: Значення прогресу (0.0 - 1.0)
        """
        self.progress_bar.set(value)


class AnimatedDropZone(ctk.CTkFrame):
    """Анімована зона для Drag & Drop з візуальними ефектами."""
    
    def __init__(self, master, **kwargs):
        """
        Ініціалізація Drag & Drop зони.
        
        Args:
            master: Батьківський віджет
            **kwargs: Додаткові параметри
        """
        # Стандартні кольори
        default_kwargs = {
            "corner_radius": 10,
            "border_width": 2,
            "border_color": "#1f6aa5",
            "fg_color": "transparent"
        }
        default_kwargs.update(kwargs)
        
        super().__init__(master, **default_kwargs)
        
        self.default_border_color = "#1f6aa5"
        self.hover_border_color = "#3e8bc7"
        self.active_border_color = "#5a9fd4"
        
        # Центральний контент
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Іконка
        self.icon_label = ctk.CTkLabel(
            content_frame,
            text="📎",
            font=ctk.CTkFont(size=48)
        )
        self.icon_label.pack(pady=(20, 10))
        
        # Основний текст
        main_text = ctk.CTkLabel(
            content_frame,
            text="Перетягніть файли сюди",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        main_text.pack(pady=5)
        
        # Допоміжний текст
        helper_text = ctk.CTkLabel(
            content_frame,
            text="або натисніть кнопку 'Додати файли'",
            font=ctk.CTkFont(size=12),
            text_color=("#6c757d", "gray60")
        )
        helper_text.pack(pady=(0, 10))
        
        # Підтримувані формати
        formats_text = ctk.CTkLabel(
            content_frame,
            text="Підтримувані формати: .doc, .docx",
            font=ctk.CTkFont(size=10),
            text_color=("#868e96", "gray50")
        )
        formats_text.pack(pady=(0, 20))
    
    def animate_hover(self):
        """Анімація при наведенні."""
        self.configure(border_color=self.hover_border_color)
        self.icon_label.configure(text="📥")
    
    def animate_leave(self):
        """Анімація при виході."""
        self.configure(border_color=self.default_border_color)
        self.icon_label.configure(text="📎")
    
    def animate_drop(self):
        """Анімація при скиданні файлів."""
        self.configure(border_color=self.active_border_color)
        # Повернення до нормального стану через 200мс
        self.after(200, self.animate_leave)
