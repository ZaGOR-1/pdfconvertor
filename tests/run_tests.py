"""
Скрипт для запуску всіх тестів
==============================

Запускає функціональні тести та тести продуктивності
"""

import unittest
import sys
from pathlib import Path

# Додаємо батьківську директорію до шляху
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_all_tests():
    """Запуск всіх тестів з звітом"""
    
    print("=" * 80)
    print("🧪 ЗАПУСК ТЕСТІВ - Word to PDF Converter")
    print("=" * 80)
    print()
    
    # Створюємо тест suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Додаємо всі тести з модулів
    try:
        from tests import test_converter, test_performance
        
        suite.addTests(loader.loadTestsFromModule(test_converter))
        suite.addTests(loader.loadTestsFromModule(test_performance))
        
        print(f"📋 Знайдено тестів: {suite.countTestCases()}\n")
        
    except ImportError as e:
        print(f"❌ Помилка імпорту тестів: {e}")
        return False
    
    # Запускаємо тести з детальним виводом
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    print("📊 РЕЗУЛЬТАТИ ТЕСТУВАННЯ")
    print("=" * 80)
    
    print(f"✅ Успішно: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Провалено: {len(result.failures)}")
    print(f"⚠️  Помилки: {len(result.errors)}")
    print(f"⏭️  Пропущено: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n🎉 ВСІ ТЕСТИ ПРОЙДЕНІ УСПІШНО!")
        return True
    else:
        print("\n⚠️  ДЕЯКІ ТЕСТИ НЕ ПРОЙДЕНІ")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
