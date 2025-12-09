"""
Main Window - GUI для Word to PDF Converter
===========================================

Головне вікно програми з використанням CustomTkinter.
"""

from typing import Optional, List, Dict
import customtkinter as ctk
from pathlib import Path
from tkinterdnd2 import DND_FILES, TkinterDnD
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Імпорт модулів конвертації
from converter.doc_converter import DocConverter
from converter.file_handler import FileHandler

# Імпорт системи тем та кастомних віджетів
from gui.theme_manager import ThemeManager
from gui.widgets import AnimatedButton, AnimatedDropZone, ThemeToggleButton
from gui.settings_window import SettingsWindow

# Імпорт конфігурації та логування
from utils.config import ConfigManager
from utils.logger import Logger
from utils.localization import Localization
from utils.update_checker import UpdateChecker
from utils.recovery_manager import RecoveryManager


class MainWindow:
    """Головне вікно програми для конвертації Word документів у PDF."""
    
    def __init__(self):
        """Ініціалізація головного вікна."""
        # Ініціалізація конфігурації та логування
        self.config = ConfigManager()
        self.logger = Logger()
        
        # Ініціалізація локалізації
        self.i18n = Localization()
        self.logger.log_app_start()
        
        # Ініціалізація менеджера тем
        self.theme_manager = ThemeManager()
        
        # Завантаження теми з конфігурації
        saved_theme = self.config.get_theme()
        self.theme_manager.set_theme(saved_theme)
        
        # Налаштування теми CustomTkinter
        ctk.set_appearance_mode(saved_theme)  # "dark" або "light"
        ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
        
        # Виправлення DPI scaling для чіткого шрифту на high DPI екранах
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)  # 1 = System DPI Aware
        except:
            pass
        
        # Створення головного вікна з підтримкою DnD
        self.root = TkinterDnD.Tk()
        self.root.title("Word to PDF Converter")
        
        # Налаштування кольорів використовуючи theme manager
        self._apply_theme_to_root()
        
        # Масштабування UI для high DPI
        try:
            self.root.tk.call('tk', 'scaling', 2.0)  # Можна налаштувати (1.0-3.0)
        except:
            pass
        
        # Налаштування розмірів вікна з конфігурації
        geometry = self.config.get_window_geometry()
        self.window_width = geometry['width']
        self.window_height = geometry['height']
        self.window_x = geometry['x']
        self.window_y = geometry['y']
        
        # Центрування вікна на екрані
        self._center_window()
        
        # Мінімальні розміри вікна
        self.root.minsize(800, 600)
        
        # Налаштування закриття вікна
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Список файлів для конвертації
        self.files_list: List[Path] = []
        
        # Віджети для файлів (зберігаємо посилання)
        self.file_widgets: List[ctk.CTkFrame] = []
        
        # Словник для зберігання прогрес барів файлів
        self.file_progress_bars: Dict[int, ctk.CTkProgressBar] = {}
        
        # Ініціалізація конвертера з налаштуваннями стиснення
        compression_settings = {
            'enable_compression': self.config.get('conversion.enable_compression', False),
            'compression_level': self.config.get('conversion.compression_level', 6)
        }
        self.converter = DocConverter(compression_settings)
        
        # Папка для збереження PDF
        self.output_folder: Optional[Path] = None
        
        # Update Checker та Recovery Manager
        self.update_checker = UpdateChecker()
        self.recovery_manager = RecoveryManager()
        
        # Багатопотоковість з пулом (динамічний max_workers)
        max_workers = self._calculate_optimal_workers()
        self.logger.info(f"Ініціалізація ThreadPool з {max_workers} worker(s)")
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="converter")
        self.conversion_thread: Optional[threading.Thread] = None
        self.is_converting = False
        self.stop_conversion = False
        
        # Створення UI елементів
        self._create_ui()
        
        # Перевірка відновлення та оновлень після запуску UI
        self.root.after(500, self._check_recovery)
        if self.config.get('general.check_updates', True):
            self.root.after(1000, self._check_updates)
    
    def _calculate_optimal_workers(self) -> int:
        """Розрахунок оптимальної кількості worker потоків.
        
        Returns:
            Кількість worker потоків
        """
        import os
        try:
            import psutil
            has_psutil = True
        except ImportError:
            has_psutil = False
        
        try:
            # Отримання кількості CPU ядер
            cpu_count = os.cpu_count() or 4
            
            # Базовий розрахунок: CPU_COUNT - 1 (залишити одне ядро для UI)
            workers = max(1, cpu_count - 1)
            
            # Обмеження за пам'яттю (якщо є psutil)
            if has_psutil:
                memory = psutil.virtual_memory()
                available_memory_gb = memory.available / (1024**3)
                # Кожен worker ~ 500MB
                max_by_memory = int(available_memory_gb / 0.5)
                workers = min(workers, max_by_memory)
                self.logger.info(f"Розраховано workers: {workers} (CPU: {cpu_count}, RAM: {available_memory_gb:.1f}GB)")
            else:
                self.logger.info(f"Розраховано workers: {workers} (CPU: {cpu_count})")
            
            # Обмеження до розумних меж (1-8)
            workers = max(1, min(workers, 8))
            
            # Перевірка конфігурації
            config_workers = self.config.get('performance.max_workers', None)
            if config_workers and isinstance(config_workers, int) and config_workers > 0:
                workers = min(workers, config_workers)
            
            return workers
            
        except Exception as e:
            self.logger.warning(f"Помилка розрахунку workers: {e}. Використовується значення за замовчуванням: 2")
            return 2
        
    def _apply_theme_to_root(self):
        """Застосування кольорів теми до головного вікна."""
        bg_color = self.theme_manager.get_color("bg_primary")
        self.root.configure(bg=bg_color)
        # Оновити header якщо він існує
        if hasattr(self, 'header_frame'):
            header_bg = "#ffffff" if self.theme_manager.current_theme == "light" else "#1f1f1f"
            self.header_frame.configure(fg_color=header_bg)
        # Кнопка теми оновлюється сама через _toggle_theme
    
    def _center_window(self):
        """Центрування вікна на екрані або відновлення збереженої позиції."""
        # Якщо є збережена позиція, використовуємо її
        if self.window_x is not None and self.window_y is not None:
            x = self.window_x
            y = self.window_y
        else:
            # Отримання розмірів екрану
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Обчислення позиції (центр)
            x = (screen_width - self.window_width) // 2
            y = (screen_height - self.window_height) // 2
        
        # Встановлення геометрії
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
        
    def _create_ui(self):
        """Створення всіх UI елементів."""
        # Налаштування сітки для головного вікна
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Створення елементів
        self._create_header()
        self._create_main_content()
        self._create_button_panel()
        self._create_status_bar()
        
        # Перевірка відновлення та оновлень після створення UI
        self.root.after(500, self._check_recovery)
        self.root.after(1000, self._check_updates)
        
    def _create_header(self):
        """Створення заголовка програми."""
        self.header_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color=("#ffffff", "#1f1f1f"))
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        
        # Кнопка перемикання теми (в правому верхньому куті)
        self.theme_toggle = ThemeToggleButton(
            self.header_frame,
            on_toggle=self._on_theme_toggle
        )
        self.theme_toggle.place(relx=0.96, rely=0.5, anchor="e")
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self.header_frame,
            text=self.i18n.get("app_title"),
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Підзаголовок
        subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text=self.i18n.get("app_subtitle"),
            font=ctk.CTkFont(size=12),
            text_color=("#495057", "gray40")
        )
        subtitle_label.pack(pady=(0, 20))
        
    def _create_main_content(self):
        """Створення основного контенту."""
        # Головний контейнер
        main_frame = ctk.CTkFrame(self.root)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Drag & Drop область (стилізована з анімаціями)
        self.drop_area = ctk.CTkFrame(
            main_frame,
            corner_radius=10,
            border_width=2,
            border_color=self.theme_manager.get_color("drop_zone_border"),
            fg_color="transparent"
        )
        self.drop_area.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        # Налаштування Drag & Drop
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self._on_drop)
        self.drop_area.dnd_bind('<<DragEnter>>', self._on_drag_enter)
        self.drop_area.dnd_bind('<<DragLeave>>', self._on_drag_leave)
        
        # Додаємо обробник кліку для вибору файлів
        self.drop_area.bind('<Button-1>', self._on_drop_area_click)
        
        # Контейнер для контенту drop zone
        drop_content = ctk.CTkFrame(self.drop_area, fg_color="transparent")
        drop_content.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Додаємо курсор-вказівник для кліку
        self.drop_area.configure(cursor="hand2")
        
        # Додаємо клік на контент також
        drop_content.bind('<Button-1>', self._on_drop_area_click)
        drop_content.configure(cursor="hand2")
        
        # Іконка
        self.drop_icon_label = ctk.CTkLabel(
            drop_content,
            text=self.i18n.get("icon_clip"),
            font=ctk.CTkFont(size=48),
            cursor="hand2"
        )
        self.drop_icon_label.pack(pady=(20, 10))
        self.drop_icon_label.bind('<Button-1>', self._on_drop_area_click)
        
        # Основний текст
        drop_text_main = ctk.CTkLabel(
            drop_content,
            text=self.i18n.get("drop_zone_title"),
            font=ctk.CTkFont(size=18, weight="bold"),
            cursor="hand2"
        )
        drop_text_main.pack(pady=5)
        drop_text_main.bind('<Button-1>', self._on_drop_area_click)
        
        # Допоміжний текст
        drop_text_helper = ctk.CTkLabel(
            drop_content,
            text=self.i18n.get("drop_zone_subtitle"),
            font=ctk.CTkFont(size=12),
            text_color=("#495057", "gray60"),
            cursor="hand2"
        )
        drop_text_helper.pack(pady=(0, 10))
        drop_text_helper.bind('<Button-1>', self._on_drop_area_click)
        
        # Підтримувані формати
        drop_formats = ctk.CTkLabel(
            drop_content,
            text=self.i18n.get("drop_zone_formats"),
            font=ctk.CTkFont(size=10),
            text_color=("#6c757d", "gray50"),
            cursor="hand2"
        )
        drop_formats.pack(pady=(0, 20))
        drop_formats.bind('<Button-1>', self._on_drop_area_click)
        
        # Контейнер для списку файлів (з прокруткою)
        self.files_container_frame = ctk.CTkScrollableFrame(
            main_frame,
            corner_radius=10,
            fg_color=("gray85", "gray20")
        )
        self.files_container_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        self.files_container_frame.grid_columnconfigure(0, weight=1)
        
    def _create_button_panel(self):
        """Створення панелі з кнопками управління."""
        button_frame = ctk.CTkFrame(self.root, corner_radius=0)
        button_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        
        # Налаштування сітки для центрування кнопок
        button_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Загальний прогрес бар (спочатку прихований)
        self.overall_progress = ctk.CTkProgressBar(
            button_frame,
            width=400,
            height=20
        )
        self.overall_progress.grid(row=0, column=0, columnspan=4, padx=20, pady=(0, 10))
        self.overall_progress.set(0)
        self.overall_progress.grid_remove()  # Сховати до початку конвертації
        
        # Кнопка "Вибрати папку" з hover ефектом
        self.btn_select_folder = ctk.CTkButton(
            button_frame,
            text=self.i18n.get("icon_folder"),
            width=40,
            height=40,
            font=ctk.CTkFont(size=18),
            fg_color=("#17a2b8", "#117a8b"),
            command=self._on_select_output_folder
        )
        self.btn_select_folder.grid(row=1, column=0, padx=5, pady=10)
        self.theme_manager.apply_hover_effect(
            self.btn_select_folder,
            enter_color=("#138496", "#0c5460"),
            leave_color=("#17a2b8", "#117a8b")
        )
        
        # Кнопка "Конвертувати" з hover ефектом
        self.btn_convert = ctk.CTkButton(
            button_frame,
            text=self.i18n.get("btn_convert"),
            width=200,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#198754", "darkgreen"),
            command=self._on_convert
        )
        self.btn_convert.grid(row=1, column=1, padx=5, pady=10)
        self.theme_manager.apply_hover_effect(
            self.btn_convert,
            enter_color=("#157347", "#2d8f45"),
            leave_color=("#198754", "darkgreen")
        )
        
        # Кнопка "Очистити список" з hover ефектом
        self.btn_clear = ctk.CTkButton(
            button_frame,
            text=self.i18n.get("btn_clear"),
            width=160,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color=("#6c757d", "gray25"),
            command=self._on_clear
        )
        self.btn_clear.grid(row=1, column=2, padx=5, pady=10)
        self.theme_manager.apply_hover_effect(
            self.btn_clear,
            enter_color=("#5a6268", "#3b3b3b"),
            leave_color=("#6c757d", "gray25")
        )
        
        # Кнопка "Налаштування" з hover ефектом
        self.btn_settings = ctk.CTkButton(
            button_frame,
            text="⚙️",
            width=40,
            height=40,
            font=ctk.CTkFont(size=18),
            fg_color=("#6c757d", "gray25"),
            command=self._on_settings
        )
        self.btn_settings.grid(row=1, column=3, padx=5, pady=10)
        self.theme_manager.apply_hover_effect(
            self.btn_settings,
            enter_color=("#5a6268", "#3b3b3b"),
            leave_color=("#6c757d", "gray25")
        )
        
    def _create_status_bar(self):
        """Створення статус бару."""
        status_frame = ctk.CTkFrame(self.root, corner_radius=0, height=40)
        status_frame.grid(row=3, column=0, sticky="ew", padx=0, pady=0)
        
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
            text_color=("#6c757d", "gray40")
        )
        version_label.pack(side="right", padx=20, pady=10)
        
    # Обробники подій (stubs)
    
    def _on_drop_area_click(self, event=None):
        """Обробник кліку на область drag & drop - відкриває діалог вибору файлів.
        
        Args:
            event: Подія кліку миші
        """
        self.update_status(self.i18n.get("status_selecting_files"))
        
        # Діалог вибору файлів
        file_types = [
            (self.i18n.get("filetype_word_docs"), "*.doc *.docx"),
            (self.i18n.get("filetype_doc"), "*.doc"),
            (self.i18n.get("filetype_docx"), "*.docx"),
            (self.i18n.get("filetype_all"), "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title=self.i18n.get("dialog_select_files"),
            filetypes=file_types
        )
        
        if files:
            self._add_files([Path(f) for f in files])
            self.logger.info(f"Користувач додав {len(files)} файл(ів) через діалог")
            self.update_status(self.i18n.get("status_files_added", count=len(files)))
        else:
            self.update_status(self.i18n.get("status_ready"))
    
    def _on_drop(self, event):
        """Обробник події drop (перетягування файлів та папок).
        
        Args:
            event: Подія DnD з даними про файли
        """
        # Отримання шляхів файлів
        files_str = event.data
        print(f"🔍 RAW DROP DATA: '{files_str}'")
        
        # Парсинг шляхів (tkinterdnd2 повертає шляхи у фігурних дужках)
        files = []
        
        # Використовуємо regex для правильного парсингу
        import re
        # Шукаємо всі шляхи у фігурних дужках або без них
        pattern = r'\{([^}]+)\}|(\S+)'
        matches = re.findall(pattern, files_str)
        files = [match[0] if match[0] else match[1] for match in matches]
        
        # DEBUG: показати що прийшло
        print(f"🔍 DEBUG - Розпарсені файли: {files}")
        
        # Конвертація у абсолютні шляхи та збір Word файлів
        word_files = []
        directories = []
        
        for f in files:
            # Очищуємо шлях від лапок та зайвих символів
            clean_path = f.strip().strip('{}').strip('"').strip("'")
            path = Path(clean_path).resolve()
            
            print(f"🔍 DEBUG - Очищений шлях: '{clean_path}'")
            
            # Перевіряємо чи це директорія
            if path.exists() and path.is_dir():
                print(f"📁 DEBUG - Це директорія: {path}")
                directories.append(path)
            elif self._is_word_file(clean_path):
                print(f"📄 DEBUG - Є Word файл")
                if path.exists():
                    word_files.append(path)
                    self.logger.info(f"Додано файл: {path}")
                else:
                    self.logger.warning(f"Файл не знайдено: {clean_path}")
            else:
                print(f"🔍 DEBUG - НЕ є Word документом")
        
        # Обробка директорій - шукаємо Word файли
        if directories:
            from converter.file_handler import FileHandler
            for directory in directories:
                print(f"🔎 Пошук Word файлів у: {directory}")
                found_files = FileHandler.get_word_files_from_directory(directory, recursive=True)
                print(f"✅ Знайдено {len(found_files)} файл(ів)")
                word_files.extend(found_files)
        
        if word_files:
            self._add_files(word_files)
            self.logger.info(f"Користувач перетягнув {len(word_files)} файл(ів)")
            self.update_status(self.i18n.get("status_files_added", count=len(word_files)))
        else:
            self.logger.warning("Перетягнуті елементи не містять Word файлів")
            self.update_status(self.i18n.get("status_no_word_files"))
        
        # Повернення до нормального вигляду з анімацією
        self.drop_area.configure(border_color=self.theme_manager.get_color("drop_zone_border"))
        self.drop_icon_label.configure(text=self.i18n.get("icon_clip"))
    
    def _on_drag_enter(self, event):
        """Обробник наведення файлів на Drag & Drop область з анімацією."""
        self.drop_area.configure(border_color=self.theme_manager.get_color("accent_hover"))
        self.drop_icon_label.configure(text=self.i18n.get("icon_download"))
    
    def _on_drag_leave(self, event):
        """Обробник виходу курсора з Drag & Drop області з анімацією."""
        self.drop_area.configure(border_color=self.theme_manager.get_color("drop_zone_border"))
        self.drop_icon_label.configure(text=self.i18n.get("icon_clip"))
    
    def _is_word_file(self, filepath: str) -> bool:
        """Перевірка, чи є файл Word документом.
        
        Args:
            filepath: Шлях до файлу
            
        Returns:
            True, якщо файл має розширення .doc або .docx
        """
        return filepath.lower().endswith(('.doc', '.docx'))
    
    def _add_files(self, files: List[Path]):
        """Додавання файлів до списку.
        
        Args:
            files: Список шляхів до файлів
        """
        added_count = 0
        for file_path in files:
            # Перевірка на дублікати
            if file_path not in self.files_list:
                self.files_list.append(file_path)
                self._create_file_widget(file_path)
                added_count += 1
        
        if added_count > 0:
            self.logger.info(f"Додано {added_count} нових файлів до списку (всього: {len(self.files_list)})")
    
    def _create_file_widget(self, file_path: Path):
        """Створення віджета для відображення файлу.
        
        Args:
            file_path: Шлях до файлу
        """
        file_index = len(self.file_widgets)
        
        # Контейнер для файлу
        file_frame = ctk.CTkFrame(
            self.files_container_frame,
            corner_radius=8,
            fg_color=("gray90", "gray17")
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
        
        # Прогрес бар (спочатку прихований)
        progress_bar = ctk.CTkProgressBar(
            file_frame,
            width=200,
            height=8,
            mode="indeterminate"
        )
        progress_bar.grid(row=1, column=1, sticky="w", padx=5, pady=(2, 10))
        progress_bar.set(0)
        progress_bar.grid_remove()  # Сховати до початку конвертації
        
        # Зберігаємо прогрес бар
        self.file_progress_bars[file_index] = progress_bar
        
        # Розмір файлу
        size_mb = file_path.stat().st_size / (1024 * 1024)
        size_text = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{file_path.stat().st_size / 1024:.0f} KB"
        
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
            file_frame,
            text=self.i18n.get("file_waiting"),
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
            width=100
        )
        status_label.grid(row=0, column=3, padx=5, pady=10, rowspan=2)
        
        # Кнопка видалення
        delete_btn = ctk.CTkButton(
            file_frame,
            text="✕",
            width=30,
            height=30,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=("gray70", "gray25"),
            hover_color=("red", "darkred"),
            command=lambda: self._remove_file(file_path, file_frame, file_index)
        )
        delete_btn.grid(row=0, column=4, padx=10, pady=10, rowspan=2)
        
        # Зберігаємо посилання на віджет
        self.file_widgets.append(file_frame)
    
    def _remove_file(self, file_path: Path, widget: ctk.CTkFrame, file_index: int):
        """Видалення файлу зі списку.
        
        Args:
            file_path: Шлях до файлу
            widget: Віджет файлу
            file_index: Індекс файлу
        """
        if file_path in self.files_list:
            self.files_list.remove(file_path)
        
        if widget in self.file_widgets:
            self.file_widgets.remove(widget)
        
        # Видалення прогрес бару
        if file_index in self.file_progress_bars:
            del self.file_progress_bars[file_index]
        
        widget.destroy()
        self.update_status(self.i18n.get("status_file_removed", name=file_path.name))
    
    def _on_select_output_folder(self):
        """Обробник вибору папки для збереження PDF."""
        # Завантаження останньої папки з конфігурації
        initial_dir = self.config.get_last_output_folder()
        
        folder = filedialog.askdirectory(
            title=self.i18n.get("dialog_select_output_folder"),
            initialdir=initial_dir
        )
        
        if folder:
            self.output_folder = Path(folder)
            # Збереження папки в конфігурацію
            self.config.set_last_output_folder(str(self.output_folder))
            self.logger.info(f"📂 Обрано папку збереження: {self.output_folder}")
            self.update_status(f"📂 Папка: {self.output_folder.name}")
            
            # Змінюємо колір кнопки щоб показати, що папка обрана
            self.btn_select_folder.configure(fg_color=("#28a745", "#1e7e34"))
        else:
            self.update_status(self.i18n.get("status_ready"))
        
    def _on_convert(self):
        """Обробник натискання кнопки 'Конвертувати'."""
        # Перевірка наявності файлів
        if not self.files_list:
            messagebox.showwarning(
                self.i18n.get("msg_no_files"),
                self.i18n.get("msg_no_files_desc")
            )
            return
        
        # Перевірка, чи не йде конвертація
        if self.is_converting:
            messagebox.showinfo(
                self.i18n.get("msg_converting"),
                self.i18n.get("msg_converting_desc")
            )
            return
        
        # Підтвердження
        result = messagebox.askyesno(
            self.i18n.get("msg_convert_confirm"),
            self.i18n.get("msg_convert_question", count=len(self.files_list))
        )
        
        if not result:
            self.logger.info("Користувач скасував конвертацію")
            return
        
        self.logger.info(f"🚀 Початок конвертації {len(self.files_list)} файл(ів)")
        
        # Показати прогрес бар
        self.overall_progress.grid()
        self.overall_progress.set(0)
        
        # Запуск конвертації в окремому потоці
        self.is_converting = True
        self.stop_conversion = False
        self.conversion_thread = threading.Thread(target=self._perform_conversion_threaded, daemon=True)
        self.conversion_thread.start()
        
        # Зміна кнопки на "Зупинити"
        self.btn_convert.configure(
            text=self.i18n.get("btn_stop"),
            fg_color=("orange", "darkorange"),
            command=self._on_stop_conversion
        )
        
        # Вимкнення інших кнопок
        self.btn_clear.configure(state="disabled")
        self.btn_select_folder.configure(state="disabled")
    
    def _on_stop_conversion(self):
        """Обробник зупинки конвертації."""
        result = messagebox.askyesno(
            self.i18n.get("msg_stop_title"),
            self.i18n.get("msg_stop_question")
        )
        
        if result:
            self.stop_conversion = True
            self.update_status(self.i18n.get("status_stopping"))
    
    def _perform_conversion_threaded(self):
        """Виконання конвертації файлів у окремому потоці."""
        start_time = time.time()
        success_count = 0
        fail_count = 0
        total_files = len(self.files_list)
        
        # Списки для відстеження оброблених файлів
        processed_indices = []
        failed_indices = []
        
        # Логування початку пакетної конвертації
        self.logger.log_batch_start(total_files)
        
        for i, file_path in enumerate(self.files_list):
            # Перевірка на зупинку
            if self.stop_conversion:
                self._update_file_status_safe(i, self.i18n.get("file_stopped"))
                self.logger.warning(f"Конвертацію зупинено користувачем на файлі {i+1}/{total_files}")
                break
            
            # Оновлення загального прогресу
            progress = i / total_files
            self.root.after(0, lambda p=progress: self.overall_progress.set(p))
            
            # Показати прогрес бар файлу та запустити анімацію
            self.root.after(0, lambda idx=i: self._show_file_progress(idx))
            
            # Оновлення статусу файлу
            self._update_file_status_safe(i, self.i18n.get("file_converting"))
            
            # Валідація файлу
            is_valid, error_msg = FileHandler.validate_file(file_path)
            
            if not is_valid:
                self._update_file_status_safe(i, f"❌ {error_msg}")
                self.root.after(0, lambda idx=i: self._hide_file_progress(idx))
                self.logger.warning(f"Валідація не пройдена для {file_path.name}: {error_msg}")
                fail_count += 1
                continue
            
            # Визначення вихідного шляху з автонумерацією
            auto_number = self.config.get("conversion.auto_number_files", False)
            output_path = FileHandler.get_output_path(file_path, self.output_folder, auto_number=auto_number)
            
            # Перевірка вільного місця на диску
            if self.output_folder:
                estimated_size = FileHandler.estimate_pdf_size(file_path)
                has_space, space_msg = FileHandler.check_disk_space(self.output_folder, estimated_size)
                
                if not has_space:
                    self._update_file_status_safe(i, f"❌ {space_msg}")
                    self.root.after(0, lambda idx=i: self._hide_file_progress(idx))
                    self.logger.error(f"Недостатньо місця на диску для {file_path.name}: {space_msg}")
                    fail_count += 1
                    continue
            
            # Перевірка чи файл існує (якщо ввімкнено запит підтвердження)
            ask_overwrite = self.config.get("conversion.ask_overwrite", True)
            if ask_overwrite and output_path.exists():
                # Запитуємо підтвердження в головному потоці
                overwrite_result = [False]  # Обгортка для зміни з callback
                
                def ask_user():
                    result = messagebox.askyesno(
                        self.i18n.get("dialog_file_exists_title"),
                        self.i18n.get("dialog_file_exists_message", name=output_path.name),
                        icon='warning'
                    )
                    overwrite_result[0] = result
                
                self.root.after(0, ask_user)
                
                # Чекаємо відповідь (простий спінлок, бо це background thread)
                import time as time_module
                timeout = 30  # 30 секунд таймаут
                waited = 0
                while waited < timeout:
                    if overwrite_result[0] or self.stop_conversion:
                        break
                    time_module.sleep(0.1)
                    waited += 0.1
                
                if not overwrite_result[0]:
                    self._update_file_status_safe(i, "⏭️ Пропущено")
                    self.root.after(0, lambda idx=i: self._hide_file_progress(idx))
                    self.logger.info(f"Конвертацію {file_path.name} пропущено користувачем")
                    continue
            
            # Логування початку конвертації
            self.logger.log_conversion_start(str(file_path), str(output_path))
            file_start_time = time.time()
            
            # Конвертація
            success, message = self.converter.convert_to_pdf(file_path, output_path)
            file_duration = time.time() - file_start_time
            
            # Оновлення статусу та логування
            if success:
                self._update_file_status_safe(i, self.i18n.get("file_completed"))
                self.logger.log_conversion_success(str(file_path), file_duration)
                success_count += 1
                processed_indices.append(i)
            else:
                self._update_file_status_safe(i, self.i18n.get("file_failed"))
                self.logger.log_conversion_error(str(file_path), message)
                fail_count += 1
                failed_indices.append(i)
            
            # Збереження стану кожні 5 файлів
            if (i + 1) % 5 == 0:
                self.recovery_manager.save_state(
                    self.files_list,
                    self.output_folder,
                    processed_indices,
                    failed_indices
                )
            
            # Сховати прогрес бар файлу
            self.root.after(0, lambda idx=i: self._hide_file_progress(idx))
        
        # Завершення
        elapsed_time = time.time() - start_time
        
        # Логування завершення пакетної конвертації
        self.logger.log_batch_complete(success_count, fail_count, elapsed_time)
        
        # Очищення стану відновлення після успішного завершення
        self.recovery_manager.clear_state()
        
        self.root.after(0, lambda: self._finish_conversion(success_count, fail_count, elapsed_time))
    
    def _show_file_progress(self, file_index: int):
        """Показати та запустити анімацію прогрес бару файлу."""
        if file_index in self.file_progress_bars:
            progress_bar = self.file_progress_bars[file_index]
            progress_bar.grid()
            progress_bar.start()
    
    def _hide_file_progress(self, file_index: int):
        """Сховати прогрес бар файлу."""
        if file_index in self.file_progress_bars:
            progress_bar = self.file_progress_bars[file_index]
            progress_bar.stop()
            progress_bar.grid_remove()
    
    def _update_file_status_safe(self, file_index: int, status: str):
        """Потокобезпечне оновлення статусу файлу."""
        self.root.after(0, lambda: self._update_file_status(file_index, status))
        
        # Також оновлюємо статус бар
        elapsed = f"Файл {file_index + 1}/{len(self.files_list)}"
        self.root.after(0, lambda msg=f"🔄 {status} - {elapsed}": self.update_status(msg))
    
    def _finish_conversion(self, success: int, failed: int, elapsed_time: float):
        """Завершення процесу конвертації.
        
        Args:
            success: Кількість успішних конвертацій
            failed: Кількість невдалих конвертацій
            elapsed_time: Час виконання в секундах
        """
        # Сховати загальний прогрес бар
        self.overall_progress.set(1.0)
        self.root.after(500, lambda: self.overall_progress.grid_remove())
        
        # Відновлення кнопок
        self.is_converting = False
        self.btn_convert.configure(
            text="🔄 Конвертувати",
            fg_color=("green", "darkgreen"),
            command=self._on_convert
        )
        self.btn_clear.configure(state="normal")
        self.btn_select_folder.configure(state="normal")
        
        # Форматування часу
        if elapsed_time < 60:
            time_str = f"{elapsed_time:.1f} {self.i18n.get('time_seconds')}"
        else:
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            time_str = f"{minutes} {self.i18n.get('time_minutes')} {seconds} {self.i18n.get('time_seconds')}"
        
        # Показати результати (якщо ввімкнено сповіщення)
        show_notifications = self.config.get("conversion.show_notifications", True)
        if show_notifications:
            self._show_conversion_results(success, failed, time_str)
    
    def _perform_conversion(self):
        """DEPRECATED: Старий синхронний метод конвертації.
        
        Збережено для сумісності, але більше не використовується.
        Використовується _perform_conversion_threaded() замість нього.
        """
        pass
    
    def _update_file_status(self, file_index: int, status: str):
        """Оновлення статусу конкретного файлу.
        
        Args:
            file_index: Індекс файлу в списку
            status: Новий статус
        """
        if file_index < len(self.file_widgets):
            widget = self.file_widgets[file_index]
            # Знаходимо label статусу (4-й елемент в grid)
            for child in widget.winfo_children():
                if isinstance(child, ctk.CTkLabel):
                    grid_info = child.grid_info()
                    if grid_info.get('column') == 3:  # Колонка статусу
                        child.configure(text=status)
                        break
    
    def _show_conversion_results(self, success: int, failed: int, time_str: str = ""):
        """Відображення результатів конвертації.
        
        Args:
            success: Кількість успішних конвертацій
            failed: Кількість невдалих конвертацій
            time_str: Час виконання (опціонально)
        """
        total = success + failed
        time_info = f"\n⏱️ {self.i18n.get('time_label')} {time_str}" if time_str else ""
        
        if self.stop_conversion:
            messagebox.showinfo(
                self.i18n.get("msg_stopped_title"),
                self.i18n.get("msg_stopped_text", success=success, failed=failed, total=total) + time_info
            )
            self.update_status(f"⏸️ {self.i18n.get('status_stopped')}: {success} / {total}")
        elif failed == 0:
            messagebox.showinfo(
                self.i18n.get("msg_complete_title"),
                self.i18n.get("msg_complete_success", success=success) + time_info
            )
            self.update_status(f"✅ {self.i18n.get('status_completed')}: {success}")
        else:
            messagebox.showwarning(
                self.i18n.get("msg_complete_errors"),
                self.i18n.get("msg_complete_stats", success=success, failed=failed, total=total) + time_info
            )
            self.update_status(f"⚠️ {success} / {total}")
        
    def _on_clear(self):
        """Обробник натискання кнопки 'Очистити'."""
        # Очищення списку файлів
        self.files_list.clear()
        
        # Видалення всіх віджетів
        for widget in self.file_widgets:
            widget.destroy()
        
        self.file_widgets.clear()
        
        self.update_status(self.i18n.get("status_list_cleared"))
        print(f"Список файлів очищено")
    
    def _on_settings(self):
        """Обробник натискання кнопки 'Налаштування'."""
        settings_window = SettingsWindow(
            self.root,
            self.config,
            self._on_settings_saved
        )
        settings_window.focus()
    
    def _on_settings_saved(self, settings: dict):
        """Callback після збереження налаштувань.
        
        Args:
            settings: Словник з новими налаштуваннями
        """
        self.logger.info(f"⚙️ Налаштування оновлено: {settings}")
        self.update_status(self.i18n.get("status_settings_saved"))
        
        # Оновлення налаштувань стиснення в конвертері
        if 'enable_compression' in settings or 'compression_level' in settings:
            self.converter.compression_settings = {
                'enable_compression': self.config.get('conversion.enable_compression', False),
                'compression_level': self.config.get('conversion.compression_level', 6)
            }
    
    def _on_theme_toggle(self, new_theme: str):
        """
        Обробник перемикання теми.
        
        Args:
            new_theme: Нова тема ("dark" або "light")
        """
        self.theme_manager.set_theme(new_theme)
        self._apply_theme_to_root()
        
        # Збереження теми в конфігурацію
        self.config.set_theme(new_theme)
        self.logger.log_theme_change(new_theme)
        
        theme_name = self.i18n.get("theme_dark") if new_theme == 'dark' else self.i18n.get("theme_light")
        self.update_status(self.i18n.get("status_theme_changed", theme=theme_name))
        print(f"Тему змінено на: {new_theme}")
        
    def _on_closing(self):
        """Обробник закриття вікна."""
        # Зупинка executor
        try:
            self.executor.shutdown(wait=False, cancel_futures=True)
            self.logger.debug("🔧 ThreadPoolExecutor зупинено")
        except Exception as e:
            self.logger.error(f"Помилка зупинки executor: {e}")
        
        # Збереження геометрії вікна
        try:
            # Оновлення інформації про вікно
            self.root.update_idletasks()
            
            # Отримання поточної геометрії
            geometry = self.root.geometry()
            # Формат: "WIDTHxHEIGHT+X+Y"
            parts = geometry.replace('x', '+').split('+')
            if len(parts) >= 4:
                width = int(parts[0])
                height = int(parts[1])
                x = int(parts[2])
                y = int(parts[3])
                
                self.config.set_window_geometry(width, height, x, y)
                self.logger.debug(f"💾 Геометрію вікна збережено: {width}x{height}+{x}+{y}")
        except Exception as e:
            self.logger.error(f"Помилка збереження геометрії вікна: {e}")
        
        # Логування закриття
        self.logger.log_app_exit()
        
        print("Закриття програми...")
        self.root.destroy()
    
    def _check_recovery(self):
        """Перевірка наявності незавершеної конвертації."""
        if self.recovery_manager.has_recovery_data():
            info = self.recovery_manager.get_recovery_info()
            if info:
                result = messagebox.askyesno(
                    "🔄 Відновлення конвертації",
                    info,
                    icon='question'
                )
                
                if result:
                    # Відновлення файлів
                    remaining_files = self.recovery_manager.get_remaining_files()
                    if remaining_files:
                        self._add_files(remaining_files)
                        self.logger.info(f"✅ Відновлено {len(remaining_files)} файл(ів)")
                        self.update_status(f"✅ Відновлено {len(remaining_files)} файл(ів)")
                
                # Очищуємо файл відновлення
                self.recovery_manager.clear_state()
    
    def _check_updates(self):
        """Асинхронна перевірка оновлень."""
        def on_update_check(has_update, new_version, url):
            if has_update and new_version and url:
                self.root.after(0, lambda: self._show_update_dialog(new_version, url))
        
        self.update_checker.check_for_updates_async(on_update_check)
    
    def _show_update_dialog(self, new_version: str, url: str):
        """Показати діалог про доступне оновлення.
        
        Args:
            new_version: Нова версія
            url: URL для завантаження
        """
        message = (
            f"🎉 Доступна нова версія програми!\n\n"
            f"Поточна версія: {self.update_checker.CURRENT_VERSION}\n"
            f"Нова версія: {new_version}\n\n"
            f"Відкрити сторінку завантаження?"
        )
        
        result = messagebox.askyesno(
            "🔔 Оновлення доступне",
            message,
            icon='info'
        )
        
        if result:
            import webbrowser
            webbrowser.open(url)
            self.logger.info(f"Користувач перейшов на сторінку завантаження: {url}")
        
    # Допоміжні методи
    
    def update_status(self, message: str):
        """Оновлення тексту в статус барі.
        
        Args:
            message: Повідомлення для відображення
        """
        self.status_label.configure(text=message)
        self.root.update_idletasks()
        
    def run(self):
        """Запуск головного циклу програми."""
        print("🚀 Запуск GUI...")
        self.root.mainloop()


# Тестовий запуск
if __name__ == "__main__":
    app = MainWindow()
    app.run()
