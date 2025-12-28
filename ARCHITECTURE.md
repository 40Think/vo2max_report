# Архитектура VO2max Report

Документ описывает структуру проекта и взаимосвязи компонентов.

---

## Обзор системы

```
┌─────────────────────────────────────────────────────────────────┐
│                         ВХОДНЫЕ ДАННЫЕ                          │
│   CSV (OMNIA)  │  JSON (dataMap)  │  Ручной ввод (лактат)       │
└───────┬────────────────┬───────────────────┬────────────────────┘
        │                │                   │
        ▼                ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                       ПАРСЕРЫ (parsers/)                        │
│   CsvParser    │   JsonParser     │   ParserFactory             │
└───────┬────────────────┬───────────────────────────────────────-┘
        │                │
        ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   СЕРВИСЫ (services/)                           │
│   MeasurementService  │  ComparisonService                      │
└───────┬─────────────────────────┬───────────────────────────────┘
        │                         │
        ▼                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    МОДЕЛИ (models/) → PostgreSQL                │
│   Client  │  Measurement  │  MeasurementItem  │  Threshold      │
└───────┬─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ОТЧЁТЫ (reports/)                             │
│   ReportGenerator  │  Jinja2 Templates  │  HTML/PDF             │
└───────┬─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ВЫХОДНЫЕ ДАННЫЕ                         │
│   dashboard.html (графики)  │  PDF отчёты  │  Сравнения         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Структура файлов

```
vo2max_report/
├── README.md                 # Инструкция установки
├── ARCHITECTURE.md           # Этот файл
├── .gitignore               # Исключения для git
│
└── backend/                 # Основной код
    ├── manage.py            # Django CLI
    ├── docker-compose.yml   # PostgreSQL + TimescaleDB
    ├── requirements.txt     # Python зависимости
    │
    ├── dashboard.html       # Веб-интерфейс с графиками
    ├── generate_report.py   # CLI генератор отчётов
    ├── test_parsers.py      # Тесты парсеров
    │
    ├── config/              # Django настройки
    │   ├── settings.py      # Конфигурация БД, приложений
    │   ├── urls.py          # URL маршруты
    │   └── wsgi.py          # WSGI сервер
    │
    └── core/                # Основное приложение
        ├── models/          # ORM модели
        ├── parsers/         # Парсеры форматов
        ├── services/        # Бизнес-логика
        └── reports/         # Генерация отчётов
```

---

## Модели данных (core/models/)

| Файл | Модель | Назначение |
|------|--------|------------|
| `client.py` | `Client` | Профиль спортсмена (имя, вес, рост, возраст) |
| `measurement.py` | `Measurement` | Один тест (дата, протокол, тип спорта) |
| `measurement_item.py` | `MeasurementItem` | Строка данных (время, VO2, HR, мощность) |
| `threshold.py` | `Threshold` | Порог (АэП, АнП, МПК) — ручной или авто |

### Связи

```
Client (1) ─────< Measurement (N)
                      │
                      ├────< MeasurementItem (N)
                      │
                      └────< Threshold (N)
```

---

## Парсеры (core/parsers/)

| Файл | Класс | Формат |
|------|-------|--------|
| `base.py` | `BaseParser` | Абстрактный базовый класс |
| `csv_parser.py` | `CsvParser` | COSMED OMNIA CSV |
| `json_parser.py` | `JsonParser` | Custom JSON (dataMap) |
| `factory.py` | `ParserFactory` | Автоматический выбор парсера |

### Как работает

```python
# 1. Фабрика определяет формат и выбирает парсер
result = ParserFactory.parse("file.csv")

# 2. Парсер возвращает ParsedMeasurement
result.items        # Список ParsedItem (данные)
result.client_name  # Имя клиента (из JSON)
result.format       # 'OMNIA_CSV' или 'CUSTOM_JSON'
```

---

## Сервисы (core/services/)

| Файл | Класс | Назначение |
|------|-------|------------|
| `measurement_service.py` | `MeasurementService` | Импорт файлов → БД |
| `comparison_service.py` | `ComparisonService` | Сравнение тестов |

### MeasurementService

```python
# Импорт файла в базу данных
service = MeasurementService()
measurement = service.import_file(
    file_path="test.csv",
    client_id=1
)
```

### ComparisonService

```python
# Сравнение тестов по мощности
tests = ComparisonService.get_client_tests(client_id=1, test_type='CYCLING')
table = ComparisonService.build_power_aligned_table(tests, metric='hr')
```

---

## Отчёты (core/reports/)

| Файл | Назначение |
|------|------------|
| `__init__.py` | Классы данных (ReportData, ThresholdZone) |
| `generator.py` | ReportGenerator — рендер HTML/PDF |
| `templates/default_report.html` | Шаблон: зоны + тренировки |
| `templates/detailed_report.html` | Шаблон: пошаговые данные + матрица |

### Как работает

```python
from core.reports import create_sample_report
from core.reports.generator import ReportGenerator

data = create_sample_report()
gen = ReportGenerator()

# HTML
gen.generate_html_file(data.to_dict(), 'default_report', 'report.html')

# PDF (требует WeasyPrint)
gen.generate_pdf(data.to_dict(), 'default_report', 'report.pdf')
```

---

## Ключевые файлы

| Файл | Что делает | Запуск |
|------|------------|--------|
| `dashboard.html` | Интерактивные графики | Открыть в браузере |
| `generate_report.py` | CLI генератор | `python3 generate_report.py` |
| `test_parsers.py` | Тест парсеров | `python3 test_parsers.py` |
| `docker-compose.yml` | БД PostgreSQL | `docker compose up -d` |

---

## Поток данных

```
1. ЗАГРУЗКА
   CSV/JSON файл → ParserFactory → CsvParser/JsonParser
   
2. НОРМАЛИЗАЦИЯ
   ParsedItem → (время, VO2, HR, мощность, лактат...)
   
3. СОХРАНЕНИЕ (если БД активна)
   MeasurementService → Client + Measurement + MeasurementItem
   
4. АНАЛИЗ
   ComparisonService → таблицы сравнения по мощности
   
5. ОТЧЁТ
   ReportGenerator → Jinja2 → HTML/PDF
```

---

## Технологии

| Компонент | Технология |
|-----------|------------|
| Backend | Python 3.12, Django 5.x |
| База данных | PostgreSQL + TimescaleDB |
| Графики | Chart.js |
| Отчёты | Jinja2, WeasyPrint |
| Контейнеры | Docker Compose |
