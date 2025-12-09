"""
Status Panel - Панель статусу
============================

Компонент для відображення статусу та інформації.
"""

import customtkinter as ctk
from typing import Optional


class StatusPanel(ctk.CTkFrame):
    """Панель статусу програми."""
    
    def __init__(
        self,
        parent,
        theme_manager,
        i18n,
        **kwargs
    ):
        """Ініціалізація панелі статусу.
        
        Args:
            parent: Батьківський віджет
            theme_manager: Менеджер тем
            i18n: Система локалізації
        """
        super().__init__(parent, **kwargs)
        
        self.theme_manager = theme_manager
        self.i18n = i18n
        
        self._create_ui()
    
    def _create_ui(self):
        """Створення UI елементів."""
        # Контейнер для статусу
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.pack(fill="x", expand=True)
        
        # Статус текст
        self.status_label = ctk.CTkLabel(
            status_frame,
            text=self.i18n.get("status_ready"),
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self.status_label.pack(side="left", padx=20, pady=10)
        
        # Інформація про версію
        version_label = ctk.CTkLabel(
            status_frame,
            text=self.i18n.get("app_version"),
            font=ctk.CTkFont(size=10),
            text_color=self.theme_manager.get_color("text_secondary")
        )
        version_label.pack(side="right", padx=20, pady=10)
    
    def update_status(self, message: str):
        """Оновити статус.
        
        Args:
            message: Повідомлення для відображення
        """
        self.status_label.configure(text=message)
