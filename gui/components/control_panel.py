"""
Control Panel - Панель керування
================================

Компонент з кнопками управління конвертацією.
"""

import customtkinter as ctk
from typing import Callable, Optional, Any


class ControlPanel(ctk.CTkFrame):
    """Панель з кнопками управління."""
    
    def __init__(
        self,
        parent: Any,
        on_convert: Callable[[], None],
        on_clear: Callable[[], None],
        on_select_folder: Callable[[], None],
        on_settings: Callable[[], None],
        on_pause: Optional[Callable[[], None]] = None,  # #24 Додано callback для паузи
        theme_manager: Optional[Any] = None,
        i18n: Optional[Any] = None,
        **kwargs
    ) -> None:
        """Ініціалізація панелі управління.
        
        Args:
            parent: Батьківський віджет
            on_convert: Callback для конвертації
            on_clear: Callback для очищення
            on_select_folder: Callback для вибору папки
            on_settings: Callback для налаштувань
            on_pause: Callback для паузи (опціонально)
            theme_manager: Менеджер тем
            i18n: Система локалізації
        """
        super().__init__(parent, **kwargs)
        
        self.on_convert: Callable[[], None] = on_convert
        self.on_clear: Callable[[], None] = on_clear
        self.on_select_folder: Callable[[], None] = on_select_folder
        self.on_settings: Callable[[], None] = on_settings
        self.on_pause: Optional[Callable[[], None]] = on_pause  # #24
        self.theme_manager = theme_manager
        self.i18n = i18n
        
        self._create_ui()
    
    def _create_ui(self):
        """Створення UI елементів."""
        # Загальний прогрес бар (спочатку схований)
        self.overall_progress = ctk.CTkProgressBar(
            self,
            mode="determinate",
            height=20
        )
        self.overall_progress.grid(row=0, column=0, columnspan=4, padx=20, pady=(0, 10))
        self.overall_progress.set(0)
        self.overall_progress.grid_remove()
        
        # Кнопка "Вибрати папку"
        self.btn_select_folder = ctk.CTkButton(
            self,
            text=self.i18n.get("icon_folder") + " Папка",
            width=100,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=self.theme_manager.get_color("info"),
            command=self.on_select_folder
        )
        self.btn_select_folder.grid(row=1, column=0, padx=5, pady=10)
        self.theme_manager.apply_hover_effect(
            self.btn_select_folder,
            enter_color=self.theme_manager.get_color("info"),
            leave_color=self.theme_manager.get_color("info")
        )
        
        # Кнопка "Конвертувати"
        self.btn_convert = ctk.CTkButton(
            self,
            text=self.i18n.get("btn_convert"),
            command=self.on_convert,
            width=200,
            height=50,
            corner_radius=15,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=self.theme_manager.get_color("success")
        )
        self.btn_convert.grid(row=1, column=1, padx=10, pady=10)
        self.theme_manager.apply_hover_effect(
            self.btn_convert,
            enter_color=self.theme_manager.get_color("success"),
            leave_color=self.theme_manager.get_color("success")
        )
        
        # #24 Кнопка "Пауза" (спочатку схована)
        self.btn_pause = ctk.CTkButton(
            self,
            text="⏸️",
            command=self.on_pause if self.on_pause else lambda: None,
            width=60,
            height=50,
            corner_radius=15,
            font=ctk.CTkFont(size=18),
            fg_color=self.theme_manager.get_color("info")
        )
        self.btn_pause.grid(row=1, column=2, padx=5, pady=10)
        self.btn_pause.grid_remove()  # Спочатку схована
        self.theme_manager.apply_hover_effect(
            self.btn_pause,
            enter_color=self.theme_manager.get_color("info"),
            leave_color=self.theme_manager.get_color("info")
        )
        
        # Кнопка "Очистити"
        self.btn_clear = ctk.CTkButton(
            self,
            text=self.i18n.get("btn_clear"),
            command=self.on_clear,
            width=150,
            height=50,
            corner_radius=15,
            font=ctk.CTkFont(size=14),
            fg_color=self.theme_manager.get_color("warning")
        )
        self.btn_clear.grid(row=1, column=3, padx=10, pady=10)
        self.theme_manager.apply_hover_effect(
            self.btn_clear,
            enter_color=self.theme_manager.get_color("warning"),
            leave_color=self.theme_manager.get_color("warning")
        )
        
        # Кнопка "Налаштування"
        self.btn_settings = ctk.CTkButton(
            self,
            text=self.i18n.get("btn_settings"),
            command=self.on_settings,
            width=40,
            height=40,
            font=ctk.CTkFont(size=18),
            fg_color=self.theme_manager.get_color("settings")
        )
        self.btn_settings.grid(row=1, column=4, padx=5, pady=10)
        self.theme_manager.apply_hover_effect(
            self.btn_settings,
            enter_color=self.theme_manager.get_color("settings"),
            leave_color=self.theme_manager.get_color("settings")
        )
        
        # Центрування кнопок
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_columnconfigure(3, weight=0)
        self.grid_columnconfigure(4, weight=0)
    
    def set_converting_state(self, is_converting: bool):
        """Встановити стан конвертації.
        
        Args:
            is_converting: True якщо йде конвертація
        """
        if is_converting:
            self.btn_convert.configure(
                text=self.i18n.get("btn_stop"),
                fg_color=self.theme_manager.get_color("warning")
            )
            self.btn_clear.configure(state="disabled")
            self.btn_select_folder.configure(state="disabled")
            # #24 Показати кнопку паузи
            if self.on_pause:
                self.btn_pause.grid()
        else:
            self.btn_convert.configure(
                text=self.i18n.get("btn_convert"),
                fg_color=self.theme_manager.get_color("success")
            )
            self.btn_clear.configure(state="normal")
            self.btn_select_folder.configure(state="normal")
            # #24 Сховати кнопку паузи
            self.btn_pause.grid_remove()
    
    def set_pause_state(self, is_paused: bool):
        """#24 Встановити стан паузи.
        
        Args:
            is_paused: True якщо конвертація на паузі
        """
        if is_paused:
            self.btn_pause.configure(text="▶️")  # Іконка відновлення
        else:
            self.btn_pause.configure(text="⏸️")  # Іконка паузи
    
    def show_progress_bar(self):
        """Показати загальний прогрес бар."""
        self.overall_progress.grid()
        self.overall_progress.set(0)
    
    def hide_progress_bar(self):
        """Сховати загальний прогрес бар."""
        self.overall_progress.grid_remove()
    
    def set_progress(self, value: float):
        """Встановити значення прогресу.
        
        Args:
            value: Значення від 0.0 до 1.0
        """
        self.overall_progress.set(value)
    
    def set_convert_command(self, command: Callable):
        """Змінити команду кнопки конвертації.
        
        Args:
            command: Нова команда
        """
        self.btn_convert.configure(command=command)
