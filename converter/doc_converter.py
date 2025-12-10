"""
Document Converter - Конвертація Word документів у PDF
======================================================

Модуль для конвертації DOC та DOCX файлів у PDF формат з підтримкою стиснення.
"""

from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import logging
import platform
import os


class DocConverter:
    """Клас для конвертації Word документів у PDF."""
    
    def __init__(self, compression_settings: Optional[Dict[str, Any]] = None):
        """Ініціалізація конвертера.
        
        Args:
            compression_settings: Налаштування стиснення PDF
                {
                    'enable_compression': bool,
                    'compression_level': int (1-9)
                }
        """
        self.logger = logging.getLogger(__name__)
        self.is_windows = platform.system() == "Windows"
        self.compression_settings = compression_settings or {
            'enable_compression': False,
            'compression_level': 6
        }
        
    def convert_to_pdf(
        self, 
        input_path: Path, 
        output_path: Optional[Path] = None
    ) -> Tuple[bool, str]:
        """Конвертація Word документа у PDF.
        
        Args:
            input_path: Шлях до вхідного файлу (.doc або .docx)
            output_path: Шлях до вихідного PDF файлу (опціонально)
            
        Returns:
            Tuple[bool, str]: (успіх, повідомлення)
        """
        try:
            # Перевірка існування файлу
            if not input_path.exists():
                return False, f"Файл не знайдено: {input_path}"
            
            # Визначення вихідного шляху
            if output_path is None:
                output_path = input_path.with_suffix('.pdf')
            
            # Вибір методу конвертації залежно від розширення
            file_ext = input_path.suffix.lower()
            
            if file_ext == '.docx':
                success, message = self._convert_docx(input_path, output_path)
            elif file_ext == '.doc':
                success, message = self._convert_doc(input_path, output_path)
            else:
                return False, f"Непідтримуваний формат: {file_ext}"
            
            # Якщо конвертація успішна і увімкнено стиснення
            if success and self.compression_settings.get('enable_compression', False):
                compress_success = self._compress_pdf(output_path)
                if compress_success:
                    message += " (стиснуто)"
                    
            return success, message
                
        except Exception as e:
            error_msg = f"Помилка конвертації {input_path.name}: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _convert_docx(
        self, 
        input_path: Path, 
        output_path: Path
    ) -> Tuple[bool, str]:
        """Конвертація DOCX файлу у PDF за допомогою docx2pdf.
        
        Args:
            input_path: Шлях до DOCX файлу
            output_path: Шлях до вихідного PDF
            
        Returns:
            Tuple[bool, str]: (успіх, повідомлення)
        """
        try:
            from docx2pdf import convert
            
            # Конвертація
            convert(str(input_path), str(output_path))
            
            # Перевірка створення файлу
            if output_path.exists():
                return True, f"✅ Успішно конвертовано: {output_path.name}"
            else:
                return False, "PDF файл не було створено"
                
        except ImportError:
            return False, "Бібліотека docx2pdf не встановлена"
        except PermissionError:
            self.logger.error(f"Немає доступу до файлу {input_path.name}")
            return False, f"Файл {input_path.name} використовується іншою програмою"
        except MemoryError:
            self.logger.error(f"Недостатньо пам'яті для конвертації {input_path.name}")
            return False, "Недостатньо пам'яті для конвертації файлу"
        except OSError as e:
            self.logger.error(f"Помилка файлової системи для {input_path.name}: {e}")
            return False, f"Помилка доступу до файлу: {str(e)}"
        except Exception as e:
            self.logger.error(f"Несподівана помилка при конвертації {input_path.name}: {e}")
            return False, f"Помилка конвертації DOCX: {str(e)}"
    
    def _convert_doc(
        self, 
        input_path: Path, 
        output_path: Path
    ) -> Tuple[bool, str]:
        """Конвертація DOC файлу у PDF за допомогою MS Word (win32com).
        
        Args:
            input_path: Шлях до DOC файлу
            output_path: Шлях до вихідного PDF
            
        Returns:
            Tuple[bool, str]: (успіх, повідомлення)
        """
        if not self.is_windows:
            return False, "Конвертація .doc файлів підтримується тільки на Windows"
        
        word = None
        doc = None
        com_initialized = False
        
        try:
            import win32com.client
            import pythoncom
            import pywintypes
            
            # Ініціалізація COM
            pythoncom.CoInitialize()
            com_initialized = True
            
            # Константи для Word
            wdFormatPDF = 17
            
            # Створення об'єкта Word з timeout
            try:
                word = win32com.client.DispatchEx("Word.Application")
                word.Visible = False
                word.DisplayAlerts = 0  # Вимкнути всі діалоги
            except Exception as e:
                self.logger.error(f"Не вдалося запустити MS Word: {e}")
                return False, "MS Word не знайдено або не може бути запущений"
            
            # Відкриття документа
            try:
                doc = word.Documents.Open(
                    str(input_path.absolute()),
                    ConfirmConversions=False,
                    ReadOnly=True,
                    AddToRecentFiles=False
                )
            except pywintypes.com_error as e:
                self.logger.error(f"Помилка відкриття документа {input_path.name}: {e}")
                return False, f"Не вдалося відкрити документ: файл може бути пошкоджений"
            
            # Збереження як PDF
            try:
                doc.SaveAs(
                    str(output_path.absolute()), 
                    FileFormat=wdFormatPDF,
                    EmbedTrueTypeFonts=True
                )
            except pywintypes.com_error as e:
                self.logger.error(f"Помилка збереження PDF {output_path.name}: {e}")
                return False, f"Не вдалося створити PDF: {str(e)}"
            
            return True, f"✅ Успішно конвертовано: {output_path.name}"
            
        except ImportError:
            return False, "pywin32 не встановлено або MS Word не знайдено"
        except MemoryError:
            self.logger.error(f"Недостатньо пам'яті для конвертації {input_path.name}")
            return False, "Недостатньо пам'яті для конвертації файлу"
        except Exception as e:
            self.logger.error(f"Несподівана помилка при конвертації {input_path.name}: {e}")
            return False, f"Помилка конвертації DOC: {str(e)}"
        finally:
            # Гарантований cleanup COM об'єктів
            try:
                if doc is not None:
                    doc.Close(SaveChanges=False)
                    del doc
                    doc = None
            except:
                pass
            
            try:
                if word is not None:
                    word.Quit()
                    del word
                    word = None
            except:
                pass
            
            if com_initialized:
                try:
                    pythoncom.CoUninitialize()
                except:
                    pass
    
    def _compress_pdf(self, pdf_path: Path) -> bool:
        """Безвтратне стиснення PDF файлу з підтримкою різних рівнів.
        
        Args:
            pdf_path: Шлях до PDF файлу
            
        Returns:
            bool: True якщо стиснення успішне
        """
        try:
            import pikepdf
            from PIL import Image
            import io
            
            # Отримання розміру до стиснення
            original_size = pdf_path.stat().st_size
            
            # Рівень стиснення (1-9)
            compression_level = self.compression_settings.get('compression_level', 6)
            
            # Відкриття PDF
            pdf = pikepdf.Pdf.open(pdf_path, allow_overwriting_input=True)
            
            # Лічильники для статистики
            images_found = 0
            images_compressed = 0
            
            # === 2. Оптимізація зображень ===
            for page_num, page in enumerate(pdf.pages):
                try:
                    if '/Resources' in page and '/XObject' in page.get('/Resources', {}):
                        xobjects = page.get('/Resources').get('/XObject')
                        
                        for key in list(xobjects.keys()):
                            obj = xobjects[key]
                            
                            if isinstance(obj, pikepdf.Stream) and obj.get('/Subtype') == '/Image':
                                images_found += 1
                                
                                try:
                                    # Рівень 1: пропускаємо стиснення зображень
                                    if compression_level == 1:
                                        continue
                                    
                                    current_filter = obj.get('/Filter')
                                    raw_image = obj.read_bytes()
                                    
                                    self.logger.debug(f"Знайдено зображення: розмір={len(raw_image)}, фільтр={current_filter}")
                                    
                                    # Рівень 2: стискаємо тільки нестиснені
                                    # Рівень 3+: стискаємо все
                                    should_compress = (compression_level >= 3) or (current_filter is None or current_filter == '/FlateDecode')
                                    
                                    if should_compress:
                                        try:
                                            img = Image.open(io.BytesIO(raw_image))
                                            original_width, original_height = img.size
                                            
                                            # Конвертація CMYK/LAB в RGB
                                            if img.mode in ('CMYK', 'LAB'):
                                                img = img.convert('RGB')
                                            
                                            output = io.BytesIO()
                                            
                                            # Для кольорових та сірих зображень
                                            if img.mode in ('RGB', 'L'):
                                                # === Розширена шкала якості ===
                                                if compression_level == 1:
                                                    quality = 100  # Максимальна якість
                                                    should_resize = False
                                                elif compression_level == 2:
                                                    quality = 95  # Дуже висока
                                                    should_resize = False
                                                elif compression_level == 3:
                                                    quality = 90  # Висока
                                                    should_resize = False
                                                elif compression_level == 4:
                                                    quality = 85  # Хороша
                                                    should_resize = False
                                                elif compression_level == 5:
                                                    quality = 80  # Хороша
                                                    should_resize = original_width > 2000 or original_height > 2000
                                                elif compression_level == 6:
                                                    quality = 75  # Середня
                                                    should_resize = original_width > 1600 or original_height > 1600
                                                elif compression_level == 7:
                                                    quality = 65  # Нижче середньої
                                                    should_resize = original_width > 1400 or original_height > 1400
                                                elif compression_level == 8:
                                                    quality = 55  # Низька
                                                    should_resize = original_width > 1200 or original_height > 1200
                                                else:  # level 9
                                                    quality = 45  # Дуже низька
                                                    should_resize = original_width > 1000 or original_height > 1000
                                                
                                                # Зменшення розміру зображення для високих рівнів
                                                if should_resize:
                                                    max_size = {
                                                        5: 2000, 6: 1600, 7: 1400, 8: 1200, 9: 1000
                                                    }.get(compression_level, 2000)
                                                    
                                                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                                                
                                                # JPEG стиснення
                                                img.save(output, format='JPEG', 
                                                       quality=quality,
                                                       optimize=compression_level >= 3,
                                                       progressive=compression_level >= 5)
                                                
                                                # Оновлення зображення в PDF
                                                compressed_image = pikepdf.Stream(pdf, output.getvalue())
                                                compressed_image['/Type'] = pikepdf.Name('/XObject')
                                                compressed_image['/Subtype'] = pikepdf.Name('/Image')
                                                compressed_image['/Filter'] = pikepdf.Name('/DCTDecode')
                                                compressed_image['/Width'] = img.width
                                                compressed_image['/Height'] = img.height
                                                compressed_image['/ColorSpace'] = pikepdf.Name('/DeviceRGB') if img.mode == 'RGB' else pikepdf.Name('/DeviceGray')
                                                compressed_image['/BitsPerComponent'] = 8
                                                
                                                # Рівень 1-2: замінюємо тільки якщо зменшився розмір
                                                # Рівень 3+: завжди замінюємо
                                                if compression_level >= 3 or len(output.getvalue()) < len(raw_image):
                                                    xobjects[key] = compressed_image
                                                    images_compressed += 1
                                                    self.logger.debug(f"Зображення стиснуто: {len(raw_image)} → {len(output.getvalue())} байт")
                                                    
                                            # Для зображень з прозорістю
                                            elif img.mode == 'RGBA':
                                                # Рівень 5+: конвертуємо RGBA в RGB (втрата прозорості, але більше стиснення)
                                                if compression_level >= 5:
                                                    # Створюємо білий фон
                                                    background = Image.new('RGB', img.size, (255, 255, 255))
                                                    background.paste(img, mask=img.split()[3])  # Альфа-канал як маска
                                                    img = background
                                                    
                                                    quality = 45 if compression_level == 9 else (55 if compression_level == 8 else (65 if compression_level == 7 else (75 if compression_level == 6 else 80)))
                                                    img.save(output, format='JPEG', quality=quality, optimize=True)
                                                    
                                                    compressed_image = pikepdf.Stream(pdf, output.getvalue())
                                                    compressed_image['/Type'] = pikepdf.Name('/XObject')
                                                    compressed_image['/Subtype'] = pikepdf.Name('/Image')
                                                    compressed_image['/Filter'] = pikepdf.Name('/DCTDecode')
                                                    compressed_image['/Width'] = img.width
                                                    compressed_image['/Height'] = img.height
                                                    compressed_image['/ColorSpace'] = pikepdf.Name('/DeviceRGB')
                                                    compressed_image['/BitsPerComponent'] = 8
                                                    xobjects[key] = compressed_image
                                                else:
                                                    # Низькі рівні: PNG з оптимізацією
                                                    img.save(output, format='PNG', optimize=True, compress_level=9)
                                                    
                                                    if len(output.getvalue()) < len(raw_image):
                                                        compressed_image = pikepdf.Stream(pdf, output.getvalue())
                                                        compressed_image['/Type'] = pikepdf.Name('/XObject')
                                                        compressed_image['/Subtype'] = pikepdf.Name('/Image')
                                                        compressed_image['/Filter'] = pikepdf.Name('/FlateDecode')
                                                        compressed_image['/Width'] = img.width
                                                        compressed_image['/Height'] = img.height
                                                        xobjects[key] = compressed_image
                                                    
                                        except Exception:
                                            pass
                                            
                                except Exception:
                                    pass
                except Exception:
                    pass
            
            # === 4. Збереження у тимчасовий файл ===
            temp_path = pdf_path.with_suffix('.tmp.pdf')
            
            # === 5. Диференційовані налаштування збереження ===
            if compression_level == 1:
                # Рівень 1: мінімальні зміни
                save_settings = {
                    'compress_streams': False,  # Не стискати
                    'stream_decode_level': pikepdf.StreamDecodeLevel.none,
                    'object_stream_mode': pikepdf.ObjectStreamMode.disable,
                }
            elif compression_level == 2:
                # Рівень 2: базове стиснення
                save_settings = {
                    'compress_streams': True,
                    'stream_decode_level': pikepdf.StreamDecodeLevel.specialized,
                    'object_stream_mode': pikepdf.ObjectStreamMode.preserve,
                }
            elif compression_level <= 4:
                # Рівень 3-4: помірне стиснення
                save_settings = {
                    'compress_streams': True,
                    'stream_decode_level': pikepdf.StreamDecodeLevel.specialized,
                    'object_stream_mode': pikepdf.ObjectStreamMode.generate,
                    'normalize_content': False,
                }
            elif compression_level <= 6:
                # Рівень 5-6: сильне стиснення
                save_settings = {
                    'compress_streams': True,
                    'stream_decode_level': pikepdf.StreamDecodeLevel.generalized,
                    'object_stream_mode': pikepdf.ObjectStreamMode.generate,
                    'recompress_flate': True,
                }
            else:
                # Рівень 7-9: максимальне стиснення
                save_settings = {
                    'compress_streams': True,
                    'stream_decode_level': pikepdf.StreamDecodeLevel.generalized,
                    'object_stream_mode': pikepdf.ObjectStreamMode.generate,
                    'linearize': True,  # Лінеаризація (без normalize_content)
                    'recompress_flate': True,
                    'deterministic_id': True,
                    'min_version': '1.5',
                }
            
            pdf.save(temp_path, **save_settings)
            pdf.close()
            
            # Перевірка чи стиснення дало результат
            compressed_size = temp_path.stat().st_size
            
            if compressed_size < original_size:
                # Заміна оригінального файлу
                os.replace(temp_path, pdf_path)
                reduction = ((original_size - compressed_size) / original_size) * 100
                size_saved = (original_size - compressed_size) / 1024 / 1024  # MB
                self.logger.info(f"PDF стиснуто (рівень {compression_level}): {pdf_path.name} - зменшено на {reduction:.1f}% ({size_saved:.2f} MB). Зображень: знайдено {images_found}, стиснуто {images_compressed}")
                return True
            else:
                # Видалення тимчасового файлу, якщо стиснення не дало ефекту
                temp_path.unlink()
                self.logger.info(f"Стиснення не зменшило розмір: {pdf_path.name}. Зображень: знайдено {images_found}, стиснуто {images_compressed}")
                return False
                
        except ImportError:
            self.logger.warning("pikepdf не встановлено - стиснення недоступне")
            return False
        except Exception as e:
            self.logger.error(f"Помилка стиснення PDF: {str(e)}")
            # Видалення тимчасового файлу у випадку помилки
            temp_path = pdf_path.with_suffix('.tmp.pdf')
            if temp_path.exists():
                temp_path.unlink()
            return False
    
    def convert_batch(
        self,
        file_paths: list[Path],
        output_dir: Optional[Path] = None
    ) -> dict:
        """Пакетна конвертація списку файлів.
        
        Args:
            file_paths: Список шляхів до файлів
            output_dir: Директорія для збереження PDF (опціонально)
            
        Returns:
            dict: Словник з результатами {
                'total': загальна кількість,
                'success': кількість успішних,
                'failed': кількість невдалих,
                'results': список результатів
            }
        """
        results = {
            'total': len(file_paths),
            'success': 0,
            'failed': 0,
            'results': []
        }
        
        for file_path in file_paths:
            # Визначення вихідного шляху
            if output_dir:
                output_path = output_dir / file_path.with_suffix('.pdf').name
            else:
                output_path = file_path.with_suffix('.pdf')
            
            # Конвертація
            success, message = self.convert_to_pdf(file_path, output_path)
            
            # Збереження результату
            results['results'].append({
                'file': file_path.name,
                'success': success,
                'message': message,
                'output': str(output_path) if success else None
            })
            
            # Підрахунок статистики
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
        
        return results


# Тестування
if __name__ == "__main__":
    # Налаштування логування
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    converter = DocConverter()
    print("DocConverter ініціалізовано")
    print(f"Платформа: {platform.system()}")
    print(f"Windows: {converter.is_windows}")
