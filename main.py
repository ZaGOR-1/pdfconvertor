"""
Word to PDF Converter - Main Entry Point
=========================================

Сучасна програма для конвертації Word документів (DOC, DOCX) у PDF формат.
"""

import sys
from pathlib import Path
from gui.main_window import MainWindow
import traceback
from utils.logger import Logger


def main():
    """Головна функція запуску програми."""
    print("=" * 60)
    print("Word to PDF Converter v0.1.0")
    print("=" * 60)
    print()
    
    # Запуск GUI
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    logger = None
    try:
        logger = Logger()
        logger.info("Запуск програми")
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Програму зупинено користувачем.")
        if logger:
            logger.info("Програму зупинено користувачем (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        error_msg = f"Критична помилка: {e}"
        print(f"\n\n❌ {error_msg}")
        traceback.print_exc()
        if logger:
            logger.error(error_msg, exc_info=True)
