"""
Профілювання продуктивності додатку
===================================

Аналіз використання CPU, пам'яті та часу виконання
"""

import cProfile
import pstats
import io
import tracemalloc
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from converter.doc_converter import DocConverter
from utils.config import ConfigManager
from utils.logger import Logger


def profile_converter_initialization():
    """Профілювання ініціалізації конвертера"""
    print("\n" + "=" * 70)
    print("📊 ПРОФІЛЮВАННЯ: Ініціалізація DocConverter")
    print("=" * 70)
    
    pr = cProfile.Profile()
    pr.enable()
    
    # Ініціалізація 100 разів
    for _ in range(100):
        converter = DocConverter()
    
    pr.disable()
    
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(10)
    
    print(s.getvalue())


def profile_config_access():
    """Профілювання доступу до конфігурації"""
    print("\n" + "=" * 70)
    print("📊 ПРОФІЛЮВАННЯ: Доступ до ConfigManager")
    print("=" * 70)
    
    config = ConfigManager()
    
    pr = cProfile.Profile()
    pr.enable()
    
    # Читання 1000 разів
    for _ in range(1000):
        theme = config.get("theme")
        window = config.get("window.width")
        compression = config.get("conversion.enable_compression")
    
    pr.disable()
    
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(10)
    
    print(s.getvalue())


def measure_memory_usage():
    """Вимірювання використання пам'яті"""
    print("\n" + "=" * 70)
    print("💾 АНАЛІЗ ПАМ'ЯТІ")
    print("=" * 70)
    
    tracemalloc.start()
    
    # Базове використання
    baseline = tracemalloc.get_traced_memory()
    print(f"Базове використання: {baseline[0] / 1024 / 1024:.2f} MB")
    
    # Створюємо об'єкти
    converter = DocConverter()
    config = ConfigManager()
    logger = Logger()
    
    current, peak = tracemalloc.get_traced_memory()
    
    print(f"Поточне використання: {current / 1024 / 1024:.2f} MB")
    print(f"Пікове використання: {peak / 1024 / 1024:.2f} MB")
    print(f"Приріст: {(current - baseline[0]) / 1024 / 1024:.2f} MB")
    
    # Топ споживачів пам'яті
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    
    print("\nТОП-10 споживачів пам'яті:")
    for stat in top_stats[:10]:
        print(f"  {stat}")
    
    tracemalloc.stop()


def measure_startup_time():
    """Вимірювання часу запуску компонентів"""
    print("\n" + "=" * 70)
    print("⏱️  ЧАС ЗАПУСКУ КОМПОНЕНТІВ")
    print("=" * 70)
    
    components = [
        ("ConfigManager", lambda: ConfigManager()),
        ("Logger", lambda: Logger()),
        ("DocConverter", lambda: DocConverter()),
    ]
    
    for name, func in components:
        times = []
        for _ in range(10):
            start = time.perf_counter()
            obj = func()
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)  # В мілісекундах
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"{name}:")
        print(f"  Середній час: {avg_time:.2f} ms")
        print(f"  Мін/Макс: {min_time:.2f} / {max_time:.2f} ms")


def analyze_gui_performance():
    """Аналіз продуктивності GUI"""
    print("\n" + "=" * 70)
    print("🖥️  ПРОДУКТИВНІСТЬ GUI")
    print("=" * 70)
    
    try:
        import customtkinter as ctk
        
        # Вимірюємо час створення віджетів
        start = time.perf_counter()
        
        root = ctk.CTk()
        root.withdraw()  # Приховуємо вікно
        
        # Створюємо типові віджети
        for i in range(50):
            frame = ctk.CTkFrame(root)
            label = ctk.CTkLabel(frame, text=f"Label {i}")
            button = ctk.CTkButton(frame, text=f"Button {i}")
        
        elapsed = (time.perf_counter() - start) * 1000
        
        print(f"Створення 50 фреймів з віджетами: {elapsed:.2f} ms")
        print(f"Середній час на віджет: {elapsed/150:.2f} ms")  # 50*3 віджетів
        
        root.destroy()
        
    except Exception as e:
        print(f"⚠️  Не вдалося протестувати GUI: {e}")


def main():
    """Головна функція профілювання"""
    print("🔬 ПРОФІЛЮВАННЯ ПРОДУКТИВНОСТІ - Word to PDF Converter")
    print("=" * 70)
    
    try:
        measure_startup_time()
        measure_memory_usage()
        profile_converter_initialization()
        profile_config_access()
        analyze_gui_performance()
        
        print("\n" + "=" * 70)
        print("✅ ПРОФІЛЮВАННЯ ЗАВЕРШЕНО")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Помилка під час профілювання: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
