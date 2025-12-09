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
                "bg_primary": "#1e1e1e",
                "bg_secondary": "#252526",
                "bg_tertiary": "#2d2d30",
                
                # Кольори тексту
                "text_primary": "#e4e6eb",
                "text_secondary": "#b0b3b8",
                "text_disabled": "#6e7681",
                
                # Акцентні кольори
                "accent_primary": "#0d6efd",
                "accent_hover": "#0b5ed7",
                "accent_active": "#0a58ca",
                
                # Кнопки
                "button_bg": "#0d6efd",
                "button_hover": "#0b5ed7",
                "button_active": "#0a58ca",
                "button_disabled": "#2d2d30",
                
                # Статуси
                "success": "#238636",
                "warning": "#d29922",
                "error": "#da3633",
                "info": "#1f6feb",
                "settings": "#373e47",
                
                # Drag & Drop зона
                "drop_zone_bg": "#252526",
                "drop_zone_border": "#0d6efd",
                "drop_zone_hover": "#2d2d30",
                "drop_zone_active": "#0d6efd",
                
                # Прогрес бари
                "progress_bg": "#2d2d30",
                "progress_fill": "#0d6efd",
                
                # Рамки та роздільники
                "border": "#3e4451",
                "separator": "#3e4451",
            },
            "light": {
                # Основні кольори
                "bg_primary": "#f5f6f7",
                "bg_secondary": "#ffffff",
                "bg_tertiary": "#e8eaed",
                
                # Кольори тексту
                "text_primary": "#1c1e21",
                "text_secondary": "#65676b",
                "text_disabled": "#8a8d91",
                
                # Акцентні кольори
                "accent_primary": "#0d6efd",
                "accent_hover": "#0b5ed7",
                "accent_active": "#0a58ca",
                
                # Кнопки
                "button_bg": "#0d6efd",
                "button_hover": "#0b5ed7",
                "button_active": "#0a58ca",
                "button_disabled": "#e4e6eb",
                
                # Статуси
                "success": "#198754",
                "warning": "#d97706",
                "error": "#b91c1c",
                "info": "#0891b2",
                "settings": "#495057",
                
                # Drag & Drop зона
                "drop_zone_bg": "#f8f9fa",
                "drop_zone_border": "#0d6efd",
                "drop_zone_hover": "#e7f1ff",
                "drop_zone_active": "#0d6efd",
                
                # Прогрес бари
                "progress_bg": "#e9ecef",
                "progress_fill": "#0d6efd",
                
                # Рамки та роздільники
                "border": "#dadde1",
                "separator": "#e4e6eb",
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
