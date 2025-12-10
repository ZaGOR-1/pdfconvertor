"""
Settings Window - Вікно налаштувань програми
============================================

Вікно для налаштування параметрів конвертації PDF.
"""

import customtkinter as ctk
from typing import Callable, Dict, Any


class SettingsWindow(ctk.CTkToplevel):
    """Вікно налаштувань програми."""
    
    # Словники для мапінгу значень
    QUALITY_LABELS = {
        "low": "Низька (менший розмір)",
        "standard": "Стандартна",
        "high": "Висока",
        "maximum": "Максимальна (великий розмір)"
    }
    
    def __init__(self, parent, config_manager, on_save: Callable[[Dict[str, Any]], None]):
        """Ініціалізація вікна налаштувань.
        
        Args:
            parent: Батьківське вікно
            config_manager: Менеджер конфігурації
            on_save: Callback функція для збереження налаштувань
        """
        super().__init__(parent)
        
        self.config = config_manager
        self.on_save_callback = on_save
        
        # Налаштування вікна
        self.title("⚙️ Налаштування")
        self.geometry("600x550")
        self.minsize(500, 450)
        self.resizable(True, True)
        
        # Завантаження збереженої позиції та розмірів
        saved_x = self.config.get("settings_window.x")
        saved_y = self.config.get("settings_window.y")
        saved_width = self.config.get("settings_window.width", 600)
        saved_height = self.config.get("settings_window.height", 550)
        
        self.update_idletasks()
        
        if saved_x is not None and saved_y is not None:
            # Використовуємо збережену позицію та розміри
            self.geometry(f"{saved_width}x{saved_height}+{saved_x}+{saved_y}")
        else:
            # Центруємо вікно
            x = (self.winfo_screenwidth() // 2) - (saved_width // 2)
            y = (self.winfo_screenheight() // 2) - (saved_height // 2)
            self.geometry(f"{saved_width}x{saved_height}+{x}+{y}")
        
        # Модальність
        self.transient(parent)
        self.grab_set()
        
        # Збереження позиції при закритті
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Словник для збереження значень
        self.settings = {}
        
        # Створення інтерфейсу
        self._create_widgets()
        
    def _create_widgets(self):
        """Створення елементів інтерфейсу."""
        # Основний контейнер з прокруткою
        main_frame = ctk.CTkScrollableFrame(self, width=560, height=400)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Заголовок
        title_label = ctk.CTkLabel(
            main_frame,
            text="⚙️ Налаштування конвертації",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # === Секція: Якість PDF ===
        self._create_section_header(main_frame, "📄 Налаштування PDF")
        
        # Якість PDF
        quality_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        quality_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            quality_frame,
            text="Якість PDF:",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=(0, 10))
        
        # Отримуємо поточну якість з конфігу
        current_quality = self.config.get("conversion.pdf_quality", "standard")
        current_label = self.QUALITY_LABELS.get(current_quality, "Стандартна")
        
        self.quality_var = ctk.StringVar(value=current_label)
        quality_options = ["low", "standard", "high", "maximum"]
        
        self.quality_menu = ctk.CTkOptionMenu(
            quality_frame,
            values=[self.QUALITY_LABELS[q] for q in quality_options],
            variable=self.quality_var,
            width=300
        )
        self.quality_menu.pack(side="left")
        
        # Мапінг для зворотного перетворення
        self.quality_reverse_map = {v: k for k, v in self.QUALITY_LABELS.items()}
        
        # Орієнтація сторінки
        orientation_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        orientation_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            orientation_frame,
            text="Орієнтація:",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=(0, 10))
        
        self.orientation_var = ctk.StringVar(value=self.config.get("conversion.orientation", "portrait"))
        
        orientation_segment = ctk.CTkSegmentedButton(
            orientation_frame,
            values=["📄 Портретна", "📃 Альбомна"],
            variable=self.orientation_var,
            width=300
        )
        orientation_segment.pack(side="left")
        
        # Розмір сторінки
        pagesize_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        pagesize_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            pagesize_frame,
            text="Розмір сторінки:",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=(0, 10))
        
        self.pagesize_var = ctk.StringVar(value=self.config.get("conversion.page_size", "A4"))
        
        pagesize_menu = ctk.CTkOptionMenu(
            pagesize_frame,
            values=["A4", "A3", "A5", "Letter", "Legal"],
            variable=self.pagesize_var,
            width=300
        )
        pagesize_menu.pack(side="left")
        
        # === Секція: Стиснення ===
        self._create_section_header(main_frame, "🗜️ Стиснення")
        
        # Увімкнути стиснення
        self.compression_var = ctk.BooleanVar(value=self.config.get("conversion.enable_compression", False))
        
        compression_checkbox = ctk.CTkCheckBox(
            main_frame,
            text="Увімкнути стиснення PDF (зменшує розмір файлу)",
            variable=self.compression_var,
            font=ctk.CTkFont(size=14)
        )
        compression_checkbox.pack(fill="x", pady=5)
        
        # Рівень стиснення
        compression_level_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        compression_level_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            compression_level_frame,
            text="Рівень стиснення:",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=(0, 10))
        
        self.compression_level_var = ctk.IntVar(value=self.config.get("conversion.compression_level", 6))
        
        compression_slider = ctk.CTkSlider(
            compression_level_frame,
            from_=1,
            to=9,
            number_of_steps=8,
            variable=self.compression_level_var,
            width=200
        )
        compression_slider.pack(side="left", padx=(0, 10))
        
        self.compression_level_label = ctk.CTkLabel(
            compression_level_frame,
            text=str(self.compression_level_var.get()),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.compression_level_label.pack(side="left")
        
        # Оновлення мітки при зміні слайдера
        compression_slider.configure(command=lambda v: self.compression_level_label.configure(text=str(int(v))))
        
        # === Секція: Загальні налаштування ===
        self._create_section_header(main_frame, "🔧 Загальні налаштування")
        
        # Запитувати про перезапис
        self.ask_overwrite_var = ctk.BooleanVar(value=self.config.get("conversion.ask_overwrite", True))
        
        ask_overwrite_checkbox = ctk.CTkCheckBox(
            main_frame,
            text="Запитувати підтвердження при перезаписі існуючих файлів",
            variable=self.ask_overwrite_var,
            font=ctk.CTkFont(size=14)
        )
        ask_overwrite_checkbox.pack(fill="x", pady=5)
        
        # Показувати сповіщення
        self.show_notifications_var = ctk.BooleanVar(value=self.config.get("conversion.show_notifications", True))
        
        notifications_checkbox = ctk.CTkCheckBox(
            main_frame,
            text="Показувати сповіщення після завершення конвертації",
            variable=self.show_notifications_var,
            font=ctk.CTkFont(size=14)
        )
        notifications_checkbox.pack(fill="x", pady=5)
        
        # Автоматична нумерація файлів
        self.auto_number_var = ctk.BooleanVar(value=self.config.get("conversion.auto_number_files", False))
        
        auto_number_checkbox = ctk.CTkCheckBox(
            main_frame,
            text="Автоматична нумерація при дублікатах (file.pdf, file (1).pdf)",
            variable=self.auto_number_var,
            font=ctk.CTkFont(size=14)
        )
        auto_number_checkbox.pack(fill="x", pady=5)
        
        # Максимальний розмір файлу
        max_size_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        max_size_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            max_size_frame,
            text="Макс. розмір файлу (МБ):",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=(0, 10))
        
        self.max_file_size_var = ctk.IntVar(value=self.config.get("conversion.max_file_size_mb", 100))
        
        max_size_entry = ctk.CTkEntry(
            max_size_frame,
            textvariable=self.max_file_size_var,
            width=100
        )
        max_size_entry.pack(side="left")
        
        # === Кнопки ===
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.pack(side="bottom", fill="x", padx=20, pady=10)
        
        # Кнопка "Скасувати"
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="❌ Скасувати",
            command=self._on_closing,
            width=140,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color=("#6c757d", "gray25")
        )
        cancel_btn.pack(side="right", padx=5)
        
        # Кнопка "Зберегти"
        save_btn = ctk.CTkButton(
            buttons_frame,
            text="💾 Зберегти",
            command=self._save_settings,
            width=140,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color=("#28a745", "#1e7e34")
        )
        save_btn.pack(side="right", padx=5)
        
        # Кнопка "За замовчуванням"
        reset_btn = ctk.CTkButton(
            buttons_frame,
            text="🔄 За замовчуванням",
            command=self._reset_to_defaults,
            width=180,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color=("#17a2b8", "#117a8b")
        )
        reset_btn.pack(side="left", padx=5)
        
    def _create_section_header(self, parent, text: str):
        """Створення заголовка секції.
        
        Args:
            parent: Батьківський елемент
            text: Текст заголовка
        """
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(15, 10))
        
        label = ctk.CTkLabel(
            header_frame,
            text=text,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        label.pack(anchor="w")
        
        # Розділювач
        separator = ctk.CTkFrame(parent, height=2, fg_color=("gray70", "gray30"))
        separator.pack(fill="x", pady=(0, 10))
        
    def _save_settings(self):
        """Збереження налаштувань."""
        # Збір всіх налаштувань
        settings = {
            "enable_compression": self.compression_var.get(),
            "compression_level": self.compression_level_var.get(),
            "ask_overwrite": self.ask_overwrite_var.get(),
            "show_notifications": self.show_notifications_var.get(),
            "auto_number_files": self.auto_number_var.get(),
            "max_file_size_mb": self.max_file_size_var.get()
        }
        
        # Збереження в конфіг
        for key, value in settings.items():
            self.config.set(f"conversion.{key}", value)
        
        # Виклик callback
        if self.on_save_callback:
            self.on_save_callback(settings)
        
        # Збереження позиції і закриття вікна
        self._on_closing()
    
    def _on_closing(self):
        """Обробник закриття вікна - збереження позиції та розмірів."""
        try:
            # Оновлення інформації про вікно
            self.update_idletasks()
            
            # Отримання поточної геометрії
            geometry = self.geometry()
            # Формат: "WIDTHxHEIGHT+X+Y" або "WIDTHxHEIGHT-X-Y"
            
            # Парсинг геометрії
            # Розділяємо на розмір та позицію
            if '+' in geometry or '-' in geometry:
                # Знаходимо позицію першого + або -
                pos_index = min(
                    (geometry.find('+') if '+' in geometry else len(geometry)),
                    (geometry.find('-', 1) if '-' in geometry[1:] else len(geometry))  # Пропускаємо перший символ для від'ємних значень
                )
                
                size_part = geometry[:pos_index]
                pos_part = geometry[pos_index:]
                
                # Парсинг розміру
                width, height = map(int, size_part.split('x'))
                
                # Парсинг позиції
                pos_part = pos_part.replace('+', ' +').replace('-', ' -')
                coords = [int(x) for x in pos_part.split()]
                x, y = coords[0], coords[1] if len(coords) > 1 else coords[0]
                
                # Збереження: width={width}, height={height}, x={x}, y={y}
                
                # Збереження позиції та розмірів
                self.config.set("settings_window.x", x)
                self.config.set("settings_window.y", y)
                self.config.set("settings_window.width", width)
                self.config.set("settings_window.height", height)
                
                # Примусове збереження конфігурації
                self.config.save()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Помилка збереження геометрії вікна налаштувань: {e}")
            import traceback
            traceback.print_exc()
        
        # Закриття вікна
        self.destroy()
        
    def _reset_to_defaults(self):
        """Скидання налаштувань до значень за замовчуванням."""
        self.compression_var.set(False)
        self.compression_level_var.set(6)
        self.ask_overwrite_var.set(True)
        self.show_notifications_var.set(True)
        self.auto_number_var.set(False)
        self.max_file_size_var.set(100)
