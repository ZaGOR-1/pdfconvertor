"""
Менеджер тем для Word to PDF Converter.
Управляє світлою та темною темами інтерфейсу.
"""

from typing import Dict, Literal
import customtkinter as ctk


class ThemeManager:
    """Singleton клас для управління темами додатку."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Ініціалізація менеджера тем."""
        if self._initialized:
            return
        
        self._initialized = True
        self._current_theme: Literal["dark", "light"] = "dark"
        
        # Визначення кольорових схем для тем
        self._themes = {
            "dark": {
                # Основні кольори
                "bg_primary": "#1a1a1a",
                "bg_secondary": "#2b2b2b",
                "bg_tertiary": "#3b3b3b",
                
                # Кольори тексту
                "text_primary": "#dce4ee",
                "text_secondary": "#a0a0a0",
                "text_disabled": "#666666",
                
                # Акцентні кольори
                "accent_primary": "#1f6aa5",
                "accent_hover": "#2d7ab8",
                "accent_active": "#3e8bc7",
                
                # Кнопки
                "button_bg": "#1f6aa5",
                "button_hover": "#2d7ab8",
                "button_active": "#3e8bc7",
                "button_disabled": "#3b3b3b",
                
                # Статуси
                "success": "#28a745",
                "warning": "#ffc107",
                "error": "#dc3545",
                "info": "#17a2b8",
                
                # Drag & Drop зона
                "drop_zone_bg": "#2b2b2b",
                "drop_zone_border": "#1f6aa5",
                "drop_zone_hover": "#3b3b3b",
                "drop_zone_active": "#1f6aa5",
                
                # Прогрес бари
                "progress_bg": "#3b3b3b",
                "progress_fill": "#1f6aa5",
                
                # Рамки та роздільники
                "border": "#3b3b3b",
                "separator": "#3b3b3b",
            },
            "light": {
                # Основні кольори
                "bg_primary": "#f0f2f5",
                "bg_secondary": "#ffffff",
                "bg_tertiary": "#e4e6eb",
                
                # Кольори тексту
                "text_primary": "#212529",
                "text_secondary": "#495057",
                "text_disabled": "#adb5bd",
                
                # Акцентні кольори
                "accent_primary": "#0d6efd",
                "accent_hover": "#0b5ed7",
                "accent_active": "#0a58ca",
                
                # Кнопки
                "button_bg": "#0d6efd",
                "button_hover": "#0b5ed7",
                "button_active": "#0a58ca",
                "button_disabled": "#dee2e6",
                
                # Статуси
                "success": "#198754",
                "warning": "#ffc107",
                "error": "#dc3545",
                "info": "#0dcaf0",
                
                # Drag & Drop зона
                "drop_zone_bg": "#f8f9fa",
                "drop_zone_border": "#0d6efd",
                "drop_zone_hover": "#e7f1ff",
                "drop_zone_active": "#0d6efd",
                
                # Прогрес бари
                "progress_bg": "#e9ecef",
                "progress_fill": "#0d6efd",
                
                # Рамки та роздільники
                "border": "#ced4da",
                "separator": "#dee2e6",
            }
        }
    
    @property
    def current_theme(self) -> Literal["dark", "light"]:
        """Повертає поточну тему."""
        return self._current_theme
    
    def set_theme(self, theme: Literal["dark", "light"]) -> None:
        """
        Встановлює тему додатку.
        
        Args:
            theme: Назва теми ("dark" або "light")
        """
        if theme not in self._themes:
            raise ValueError(f"Невідома тема: {theme}")
        
        self._current_theme = theme
        # Встановити appearance mode для CustomTkinter
        ctk.set_appearance_mode(theme)
    
    def toggle_theme(self) -> Literal["dark", "light"]:
        """
        Перемикає між темною та світлою темою.
        
        Returns:
            Нова активна тема
        """
        new_theme = "light" if self._current_theme == "dark" else "dark"
        self.set_theme(new_theme)
        return new_theme
    
    def get_color(self, color_name: str) -> str:
        """
        Отримує колір для поточної теми.
        
        Args:
            color_name: Назва кольору
            
        Returns:
            Hex код кольору
        """
        theme_colors = self._themes[self._current_theme]
        return theme_colors.get(color_name, "#000000")
    
    def get_all_colors(self) -> Dict[str, str]:
        """
        Отримує всі кольори для поточної теми.
        
        Returns:
            Словник з усіма кольорами теми
        """
        return self._themes[self._current_theme].copy()
    
    def apply_hover_effect(self, widget, enter_color: str = None, leave_color: str = None):
        """
        Додає ефект наведення до віджета.
        
        Args:
            widget: CTk віджет
            enter_color: Колір при наведенні (опціонально)
            leave_color: Колір при виході (опціонально)
        """
        if enter_color is None:
            enter_color = self.get_color("accent_hover")
        if leave_color is None:
            leave_color = self.get_color("accent_primary")
        
        def on_enter(event):
            try:
                widget.configure(fg_color=enter_color)
            except:
                pass
        
        def on_leave(event):
            try:
                widget.configure(fg_color=leave_color)
            except:
                pass
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
