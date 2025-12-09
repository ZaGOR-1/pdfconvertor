# Тестування Word to PDF Converter

## Швидкий старт

### Запуск всіх тестів
```powershell
python tests/run_tests.py
```

### Запуск профілювання
```powershell
python tests/profile_app.py
```

### Запуск окремих тестів
```powershell
# Тільки функціональні тести
python -m unittest tests.test_converter

# Тільки тести продуктивності
python -m unittest tests.test_performance

# Конкретний тест
python -m unittest tests.test_converter.TestDocConverter.test_converter_initialization
```

---

## Структура тестів

```
tests/
├── __init__.py               # Пакет тестів
├── run_tests.py              # Unified test runner
├── test_converter.py         # Функціональні тести (12 тестів)
├── test_performance.py       # Тести продуктивності (8 тестів)
└── profile_app.py            # Профілювання продуктивності
```

---

## Покриття тестами

### 1. Функціональні тести (`test_converter.py`)

#### TestDocConverter
- ✅ `test_converter_initialization` - Перевірка ініціалізації конвертера
- ✅ `test_invalid_file_path` - Обробка неіснуючих файлів
- ✅ `test_unsupported_format` - Обробка непідтримуваних форматів

#### TestFileHandler
- ✅ `test_is_word_file_valid_docx` - Валідація DOCX файлів
- ✅ `test_is_word_file_valid_doc` - Валідація DOC файлів
- ✅ `test_is_word_file_invalid` - Відхилення не-Word файлів
- ✅ `test_validate_file_nonexistent` - Перевірка неіснуючих файлів
- ✅ `test_validate_file_too_large` - Перевірка файлів >100MB
- ✅ `test_get_output_path_default` - Генерація вихідних шляхів
- ✅ `test_get_output_path_with_auto_number` - Автонумерація дублікатів

#### TestCompressionLevels
- ✅ `test_compression_level_1` - Налаштування рівня 1 (мінімальне стиснення)
- ✅ `test_compression_level_9` - Налаштування рівня 9 (максимальне стиснення)

### 2. Тести продуктивності (`test_performance.py`)

#### TestPerformance
- ✅ `test_converter_initialization_speed` - Ініціалізація < 0.1s
- ✅ `test_config_load_speed` - Завантаження конфігурації < 0.05s
- ✅ `test_memory_usage_converter` - Використання пам'яті < 50MB
- ✅ `test_logger_performance` - 100 записів логів < 0.1s

#### TestScalability
- ✅ `test_handle_many_files` - Обробка 50 файлів < 1s

#### TestResourceUsage
- ✅ `test_file_handles_cleanup` - Перевірка закриття дескрипторів (потрібен psutil)

#### TestCacheOptimization
- ✅ `test_config_singleton` - ConfigManager є Singleton
- ✅ `test_logger_singleton` - Logger є Singleton

### 3. Профілювання (`profile_app.py`)

Детальний аналіз продуктивності:
- ⏱️ Час запуску компонентів (ConfigManager, Logger, DocConverter)
- 💾 Використання пам'яті (tracemalloc)
- 📊 Профілювання CPU (cProfile)
- 🖥️ Продуктивність GUI (CustomTkinter widgets)

---

## Результати останнього запуску

**Дата:** Грудень 2024  
**Всього тестів:** 20  
**Результат:** ✅ **20/20 PASSED**

### Продуктивність
- ConfigManager: **0.03 ms** ініціалізація
- Logger: **0.12 ms** ініціалізація
- DocConverter: **1.33 ms** ініціалізація
- Пам'ять: **< 1 MB** базове споживання
- GUI: **1.54 ms** на віджет

---

## Вимоги

### Обов'язкові
```
customtkinter>=5.2.2
docx2pdf>=0.1.8
pywin32>=311
pikepdf>=10.0.2
Pillow>=10.0.0
tkinterdnd2>=0.4.3
```

### Для тестування
```
psutil>=7.1.3  # Для тестів ресурсів
```

### Встановлення залежностей
```powershell
pip install -r requirements.txt
pip install psutil  # Для тестів
```

---

## Continuous Integration

### GitHub Actions (приклад)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pip install psutil
      - run: python tests/run_tests.py
```

---

## Додавання нових тестів

### 1. Функціональний тест

```python
# tests/test_converter.py

class TestMyFeature(unittest.TestCase):
    def setUp(self):
        """Виконується перед кожним тестом"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Виконується після кожного тесту"""
        shutil.rmtree(self.temp_dir)
    
    def test_my_feature(self):
        """Опис тесту"""
        # Arrange
        expected = "result"
        
        # Act
        actual = my_function()
        
        # Assert
        self.assertEqual(expected, actual)
```

### 2. Тест продуктивності

```python
# tests/test_performance.py

class TestMyPerformance(unittest.TestCase):
    def test_speed(self):
        """Перевірка швидкості"""
        start = time.perf_counter()
        
        # Код для тестування
        my_function()
        
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.1, "Занадто повільно")
```

---

## Troubleshooting

### Помилка: "No module named 'psutil'"
```powershell
pip install psutil
```

### Помилка: "FileNotFoundError" під час тестів
- Переконайтеся, що запускаєте тести з кореневої директорії проекту
- Використовуйте `python tests/run_tests.py`, а не `cd tests && python run_tests.py`

### Тести падають на великих файлах
- Переконайтеся, що маєте достатньо вільного місця на диску (>200MB)
- Тест `test_validate_file_too_large` створює файл 101MB

---

## Звіти

Детальний звіт про тестування та профілювання: **[TEST_REPORT.md](../TEST_REPORT.md)**

---

**Статус Stage 9:** ✅ **ЗАВЕРШЕНО**  
**Готовність до Stage 10:** ✅ **ТАК**
