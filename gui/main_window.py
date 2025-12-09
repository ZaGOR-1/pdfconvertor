"""
Main Window - GUI для Word to PDF Converter (Модульна версія)
============================================================

Головне вікно програми як координатор компонентів.
"""

from typing import Optional, List
import customtkinter as ctk
from pathlib import Path
from tkinterdnd2 import TkinterDnD
from tkinter import filedialog, messagebox
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import webbrowser

# Імпорт модулів конвертації
from converter.doc_converter import DocConverter
from converter.file_handler import FileHandler

# Імпорт компонентів GUI
from gui.components import DropZonePanel, FileListPanel, ControlPanel, StatusPanel
from gui.theme_manager import ThemeManager
from gui.widgets import ThemeToggleButton
from gui.settings_window import SettingsWindow

# Імпорт утиліт
from utils.config import ConfigManager
from utils.logger import Logger
from utils.localization import Localization
from utils.update_checker import UpdateChecker
from utils.recovery_manager import RecoveryManager


class MainWindow:
    """Головне вікно - координатор компонентів."""
    
    def __init__(self):
        """Ініціалізація головного вікна."""
        # Ініціалізація сервісів
        self._init_services()
        
        # Створення вікна
        self._create_window()
        
        # Створення UI компонентів
        self._create_ui()
        
        # Ініціалізація даних
        self.files_list: List[Path] = []
        self.output_folder: Optional[Path] = None
        self.is_converting = False
        self.stop_conversion = False
        self.conversion_thread: Optional[threading.Thread] = None
        
        # Перевірка відновлення та оновлень
        self.root.after(500, self._check_recovery)
        if self.config.get('general.check_updates', True):
            self.root.after(1000, self._check_updates)
    
    def _init_services(self):
        """Ініціалізація сервісів та утиліт."""
        self.config = ConfigManager()
        self.logger = Logger()
        self.i18n = Localization()
        self.theme_manager = ThemeManager()
        self.update_checker = UpdateChecker()
        self.recovery_manager = RecoveryManager()
        
        # Налаштування теми
        saved_theme = self.config.get_theme()
        self.theme_manager.set_theme(saved_theme)
        ctk.set_appearance_mode(saved_theme)
        ctk.set_default_color_theme("blue")
        
        # Ініціалізація конвертера
        compression_settings = {
            'enable_compression': self.config.get('conversion.enable_compression', False),
            'compression_level': self.config.get('conversion.compression_level', 6)
        }
        self.converter = DocConverter(compression_settings)
        
        # Налаштування FileHandler
        max_file_size = self.config.get('conversion.max_file_size_mb', 100)
        FileHandler.set_max_file_size(max_file_size)
        
        # ThreadPool
        max_workers = self._calculate_optimal_workers()
        self.logger.info(f"Ініціалізація ThreadPool з {max_workers} worker(s)")
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="converter")
        
        self.logger.log_app_start()
    
    def _create_window(self):
        """Створення головного вікна."""
        # DPI scaling
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        # Створення вікна з DnD
        self.root = TkinterDnD.Tk()
        self.root.title("Word to PDF Converter")
        self.root.configure(bg=self.theme_manager.get_color("bg_primary"))
        
        # Геометрія
        geometry = self.config.get_window_geometry()
        self.window_width = geometry['width']
        self.window_height = geometry['height']
        x = geometry.get('x')
        y = geometry.get('y')
        
        if x is not None and y is not None:
            self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
        else:
            self._center_window()
        
        self.root.minsize(800, 600)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _center_window(self):
        """Центрування вікна на екрані."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - self.window_width) // 2
        y = (screen_height - self.window_height) // 2
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
    
    def _create_ui(self):
        """Створення UI компонентів."""
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Header
        self._create_header()
        
        # Main content
        main_frame = ctk.CTkFrame(self.root)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Drop Zone
        self.drop_zone = DropZonePanel(
            main_frame,
            on_files_dropped=self._handle_files_dropped,
            on_click=self._on_select_files,
            theme_manager=self.theme_manager,
            i18n=self.i18n
        )
        self.drop_zone.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # File List
        self.file_list = FileListPanel(
            main_frame,
            on_remove_file=self._remove_file,
            theme_manager=self.theme_manager,
            i18n=self.i18n
        )
        self.file_list.grid(row=1, column=0, sticky="nsew")
        
        # Control Panel
        self.control_panel = ControlPanel(
            self.root,
            on_convert=self._on_convert,
            on_clear=self._on_clear,
            on_select_folder=self._on_select_output_folder,
            on_settings=self._on_settings,
            theme_manager=self.theme_manager,
            i18n=self.i18n
        )
        self.control_panel.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        
        # Status Panel
        self.status_panel = StatusPanel(
            self.root,
            theme_manager=self.theme_manager,
            i18n=self.i18n
        )
        self.status_panel.grid(row=3, column=0, sticky="ew")
    
    def _create_header(self):
        """Створення заголовка."""
        self.header_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color=self.theme_manager.get_color("bg_secondary"))
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        
        # Theme toggle
        self.theme_toggle = ThemeToggleButton(
            self.header_frame,
            on_toggle=self._on_theme_toggle
        )
        self.theme_toggle.place(relx=0.96, rely=0.5, anchor="e")
        
        # Title
        title_label = ctk.CTkLabel(
            self.header_frame,
            text=self.i18n.get("app_title"),
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text=self.i18n.get("app_subtitle"),
            font=ctk.CTkFont(size=12),
            text_color=self.theme_manager.get_color("text_secondary")
        )
        subtitle_label.pack(pady=(0, 20))
    
    # === Event Handlers ===
    
    def _handle_files_dropped(self, paths: List[Path]):
        """Обробка файлів після drop."""
        word_files = []
        directories = []
        
        for path in paths:
            if path.is_dir():
                directories.append(path)
            elif FileHandler.is_word_file(path):
                word_files.append(path)
        
        # Пошук у директоріях
        if directories:
            for directory in directories:
                found_files = FileHandler.get_word_files_from_directory(directory, recursive=True)
                word_files.extend(found_files)
        
        if word_files:
            self._add_files(word_files)
            self.logger.info(f"Користувач перетягнув {len(word_files)} файл(ів)")
            self.update_status(self.i18n.get("status_files_added", count=len(word_files)))
        else:
            self.logger.warning("Перетягнуті елементи не містять Word файлів")
            self.update_status(self.i18n.get("status_no_word_files"))
    
    def _on_select_files(self, event=None):
        """Вибір файлів через діалог."""
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
    
    def _add_files(self, files: List[Path]):
        """Додати файли до списку."""
        for file_path in files:
            if file_path not in self.files_list:
                self.files_list.append(file_path)
                file_index = len(self.files_list) - 1
                self.file_list.add_file(file_path, file_index)
    
    def _remove_file(self, file_path: Path, widget, file_index: int):
        """Видалити файл зі списку."""
        if file_path in self.files_list:
            self.files_list.remove(file_path)
        
        self.file_list.remove_file(widget, file_index)
        self.update_status(self.i18n.get("status_file_removed", name=file_path.name))
    
    def _on_clear(self):
        """Очистити список файлів."""
        self.files_list.clear()
        self.file_list.clear_all()
        self.update_status(self.i18n.get("status_list_cleared"))
        self.logger.info("Список файлів очищено")
    
    def _on_select_output_folder(self):
        """Вибір папки для збереження."""
        initial_dir = self.config.get_last_output_folder()
        
        folder = filedialog.askdirectory(
            title=self.i18n.get("dialog_select_output_folder"),
            initialdir=initial_dir
        )
        
        if folder:
            self.output_folder = Path(folder)
            self.config.set_last_output_folder(str(self.output_folder))
            self.logger.info(f"📂 Обрано папку збереження: {self.output_folder}")
            self.update_status(f"📂 Папка: {self.output_folder.name}")
    
    def _on_settings(self):
        """Відкрити налаштування."""
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
        
        # Оновлення максимального розміру файлу
        if 'max_file_size_mb' in settings:
            FileHandler.set_max_file_size(settings['max_file_size_mb'])
            self.logger.info(f"📏 Максимальний розмір файлу оновлено: {settings['max_file_size_mb']} МБ")
    
    def _on_theme_toggle(self, new_theme: str):
        """Перемикання теми.
        
        Args:
            new_theme: Нова тема ("dark" або "light")
        """
        self.theme_manager.set_theme(new_theme)
        self.config.set_theme(new_theme)
        ctk.set_appearance_mode(new_theme)
        
        # Оновлення кольорів
        self._refresh_theme()
        
        theme_name = self.i18n.get("theme_dark" if new_theme == "dark" else "theme_light")
        self.update_status(self.i18n.get("status_theme_changed", theme=theme_name))
        self.logger.log_theme_change(new_theme)
    
    def _refresh_theme(self):
        """Оновлення кольорів всіх компонентів при зміні теми."""
        # Root та header
        self.root.configure(bg=self.theme_manager.get_color("bg_primary"))
        self.header_frame.configure(fg_color=self.theme_manager.get_color("bg_secondary"))
        
        # Drop zone
        if hasattr(self, 'drop_zone') and hasattr(self.drop_zone, 'drop_area'):
            self.drop_zone.drop_area.configure(
                border_color=self.theme_manager.get_color("drop_zone_border"),
                fg_color=self.theme_manager.get_color("drop_zone_bg")
            )
        
        # Buttons
        if hasattr(self, 'control_panel'):
            self.control_panel.btn_convert.configure(
                fg_color=self.theme_manager.get_color("success")
            )
            self.control_panel.btn_clear.configure(
                fg_color=self.theme_manager.get_color("warning")
            )
            self.control_panel.btn_select_folder.configure(
                fg_color=self.theme_manager.get_color("info")
            )
            self.control_panel.btn_settings.configure(
                fg_color=self.theme_manager.get_color("settings")
            )
    
    def _on_convert(self):
        """Початок конвертації."""
        if not self.files_list:
            messagebox.showwarning(
                self.i18n.get("msg_no_files"),
                self.i18n.get("msg_no_files_desc")
            )
            return
        
        if self.is_converting:
            messagebox.showinfo(
                self.i18n.get("msg_converting"),
                self.i18n.get("msg_converting_desc")
            )
            return
        
        result = messagebox.askyesno(
            self.i18n.get("msg_convert_confirm"),
            self.i18n.get("msg_convert_question", count=len(self.files_list))
        )
        
        if not result:
            self.logger.info("Користувач скасував конвертацію")
            return
        
        self.logger.info(f"🚀 Початок конвертації {len(self.files_list)} файл(ів)")
        
        # UI зміни
        self.control_panel.show_progress_bar()
        self.control_panel.set_converting_state(True)
        self.control_panel.set_convert_command(self._on_stop_conversion)
        
        # Запуск конвертації
        self.is_converting = True
        self.stop_conversion = False
        self.conversion_thread = threading.Thread(target=self._perform_conversion, daemon=True)
        self.conversion_thread.start()
    
    def _on_stop_conversion(self):
        """Зупинити конвертацію."""
        result = messagebox.askyesno(
            self.i18n.get("msg_stop_title"),
            self.i18n.get("msg_stop_question")
        )
        
        if result:
            self.stop_conversion = True
            self.update_status(self.i18n.get("status_stopping"))
    
    def _perform_conversion(self):
        """Виконання конвертації (в окремому потоці)."""
        start_time = time.time()
        success_count = 0
        fail_count = 0
        processed_indices = []
        failed_indices = []
        
        self.logger.log_batch_start(len(self.files_list))
        
        for i, file_path in enumerate(self.files_list):
            if self.stop_conversion:
                break
            
            # Прогрес
            progress = i / len(self.files_list)
            self.root.after(0, lambda p=progress: self.control_panel.set_progress(p))
            
            # Показати прогрес файлу
            self.root.after(0, lambda idx=i: self.file_list.show_progress(idx))
            self.root.after(0, lambda idx=i: self.file_list.update_status(idx, self.i18n.get("file_converting")))
            
            # Валідація
            is_valid, error_msg = FileHandler.validate_file(file_path)
            
            if not is_valid:
                self.root.after(0, lambda idx=i, msg=error_msg: self.file_list.update_status(idx, f"❌ {msg}"))
                self.root.after(0, lambda idx=i: self.file_list.hide_progress(idx))
                fail_count += 1
                failed_indices.append(i)
                continue
            
            # Конвертація
            auto_number = self.config.get("conversion.auto_number_files", False)
            output_path = FileHandler.get_output_path(file_path, self.output_folder, auto_number=auto_number)
            
            # Перевірка існування файлу (тільки якщо не auto_number)
            if not auto_number and output_path.exists():
                ask_overwrite = self.config.get("conversion.ask_overwrite", True)
                if ask_overwrite:
                    # Пропускаємо файл, якщо він вже існує
                    self.root.after(0, lambda idx=i: self.file_list.update_status(idx, "⚠️ Файл існує"))
                    self.root.after(0, lambda idx=i: self.file_list.hide_progress(idx))
                    self.logger.warning(f"Файл вже існує і буде пропущений: {output_path}")
                    fail_count += 1
                    failed_indices.append(i)
                    continue
            
            # Перевірка диску
            if self.output_folder:
                estimated_size = FileHandler.estimate_pdf_size(file_path)
                has_space, space_msg = FileHandler.check_disk_space(self.output_folder, estimated_size)
                
                if not has_space:
                    self.root.after(0, lambda idx=i, msg=space_msg: self.file_list.update_status(idx, f"❌ {msg}"))
                    self.root.after(0, lambda idx=i: self.file_list.hide_progress(idx))
                    fail_count += 1
                    failed_indices.append(i)
                    continue
            
            self.logger.log_conversion_start(str(file_path), str(output_path))
            success, message = self.converter.convert_to_pdf(file_path, output_path)
            
            if success:
                self.root.after(0, lambda idx=i: self.file_list.update_status(idx, self.i18n.get("file_completed")))
                success_count += 1
                processed_indices.append(i)
            else:
                self.root.after(0, lambda idx=i: self.file_list.update_status(idx, self.i18n.get("file_failed")))
                fail_count += 1
                failed_indices.append(i)
            
            self.root.after(0, lambda idx=i: self.file_list.hide_progress(idx))
            
            # Збереження стану recovery
            if (i + 1) % 5 == 0:
                self.recovery_manager.save_state(self.files_list, self.output_folder, processed_indices, failed_indices)
        
        # Завершення
        elapsed_time = time.time() - start_time
        self.logger.log_batch_complete(success_count, fail_count, elapsed_time)
        self.recovery_manager.clear_state()
        
        self.root.after(0, lambda: self._finish_conversion(success_count, fail_count, elapsed_time))
    
    def _finish_conversion(self, success: int, failed: int, elapsed_time: float):
        """Завершення конвертації."""
        self.control_panel.set_progress(1.0)
        self.root.after(500, lambda: self.control_panel.hide_progress_bar())
        
        self.is_converting = False
        self.control_panel.set_converting_state(False)
        self.control_panel.set_convert_command(self._on_convert)
        
        # Форматування часу
        if elapsed_time < 60:
            time_str = f"{elapsed_time:.1f} {self.i18n.get('time_seconds')}"
        else:
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            time_str = f"{minutes} {self.i18n.get('time_minutes')} {seconds} {self.i18n.get('time_seconds')}"
        
        # Показати результати
        total = success + failed
        if self.config.get("conversion.show_notifications", True):
            if failed == 0:
                messagebox.showinfo(
                    self.i18n.get("msg_complete_title"),
                    self.i18n.get("msg_complete_success", success=success)
                )
            else:
                messagebox.showwarning(
                    self.i18n.get("msg_complete_errors"),
                    self.i18n.get("msg_complete_stats", success=success, failed=failed, total=total)
                )
        
        self.update_status(self.i18n.get("status_conversion_complete", success=success, failed=failed))
    
    # === Utility Methods ===
    
    def _calculate_optimal_workers(self) -> int:
        """Розрахунок оптимальної кількості workers."""
        import os
        try:
            import psutil
            has_psutil = True
        except ImportError:
            has_psutil = False
        
        try:
            cpu_count = os.cpu_count() or 4
            workers = max(1, cpu_count - 1)
            
            if has_psutil:
                memory = psutil.virtual_memory()
                available_memory_gb = memory.available / (1024**3)
                max_by_memory = int(available_memory_gb / 0.5)
                workers = min(workers, max_by_memory)
            
            workers = max(1, min(workers, 8))
            
            config_workers = self.config.get('performance.max_workers', None)
            if config_workers and isinstance(config_workers, int) and config_workers > 0:
                workers = min(workers, config_workers)
            
            return workers
        except Exception as e:
            self.logger.warning(f"Помилка розрахунку workers: {e}")
            return 2
    
    def _check_recovery(self):
        """Перевірка відновлення."""
        if self.recovery_manager.has_recovery_data():
            info = self.recovery_manager.get_recovery_info()
            if info:
                result = messagebox.askyesno("🔄 Відновлення конвертації", info, icon='question')
                
                if result:
                    remaining_files = self.recovery_manager.get_remaining_files()
                    if remaining_files:
                        self._add_files(remaining_files)
                        self.logger.info(f"✅ Відновлено {len(remaining_files)} файл(ів)")
                
                self.recovery_manager.clear_state()
    
    def _check_updates(self):
        """Перевірка оновлень."""
        def on_update_check(has_update, new_version, url):
            if has_update and new_version and url:
                self.root.after(0, lambda: self._show_update_dialog(new_version, url))
        
        self.update_checker.check_for_updates_async(on_update_check)
    
    def _show_update_dialog(self, new_version: str, url: str):
        """Показати діалог оновлення."""
        message = (
            f"🎉 Доступна нова версія програми!\n\n"
            f"Поточна версія: {self.update_checker.CURRENT_VERSION}\n"
            f"Нова версія: {new_version}\n\n"
            f"Відкрити сторінку завантаження?"
        )
        
        result = messagebox.askyesno("🔔 Оновлення доступне", message, icon='info')
        
        if result:
            webbrowser.open(url)
            self.logger.info(f"Користувач перейшов на сторінку завантаження: {url}")
    
    def _on_closing(self):
        """Обробка закриття вікна."""
        # Збереження геометрії
        geometry_str = self.root.geometry()
        parts = geometry_str.split('+')
        size_parts = parts[0].split('x')
        
        self.config.set_window_geometry(
            int(size_parts[0]),
            int(size_parts[1]),
            int(parts[1]) if len(parts) > 1 else 0,
            int(parts[2]) if len(parts) > 2 else 0
        )
        
        self.logger.log_app_exit()
        self.root.destroy()
    
    def update_status(self, message: str):
        """Оновити статус."""
        self.status_panel.update_status(message)
        self.root.update_idletasks()
    
    def run(self):
        """Запуск програми."""
        print("🚀 Запуск GUI...")
        self.root.mainloop()


# Entry point
if __name__ == "__main__":
    app = MainWindow()
    app.run()
