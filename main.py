"""
Word to PDF Converter - Main Entry Point
=========================================

Сучасна програма для конвертації Word документів (DOC, DOCX) у PDF формат.
"""

import sys
from pathlib import Path
from gui.main_window import MainWindow
import traceback


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
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Програму зупинено користувачем.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Помилка: {e}")
        traceback.print_exc()
        sys.exit(1)
