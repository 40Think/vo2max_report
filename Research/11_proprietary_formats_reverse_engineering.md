# Deep Research Plan: Реверс-инжиниринг проприетарных форматов

## Контекст

На основе исследования форматов данных (answers/1.md) выявлены проприетарные форматы, требующие детального изучения для прямого чтения без использования официального ПО производителей.

## Цели исследования

### 1. Формат Cortex .msstest

**Задачи:**
- Определить внутреннюю структуру файла (SQLite, XML, бинарный)
- Найти схему данных и таблицы
- Разработать Python-парсер для прямого чтения
- Проверить на образцах файлов

**Методы:**
- Использование hex-редакторов (xxd, HxD)
- Инструменты анализа файлов (file, binwalk)
- EF Core PowerTools для .NET форматов
- Сравнительный анализ экспорта CSV vs .msstest

**Запросы:**
1. Cortex MetaSoft Studio .msstest file format specification internal structure
2. Reverse engineering medical device data files Python
3. SQLite database reverse engineering binwalk analysis
4. EF Core PowerTools .NET database file extraction
5. MetaSoft Studio database schema tables

---

### 2. Формат COSMED .xpo

**Задачи:**
- Анализ структуры проприетарного формата .xpo
- Выявление связей с OMNIA 2.0 database
- Разработка конвертера .xpo → JSON/CSV

**Запросы:**
1. COSMED OMNIA .xpo file format reverse engineering
2. COSMED metabolic data export internal format
3. Proprietary medical device file formats analysis tools
4. COSMED K5 raw data extraction methods
5. XML-based medical device data formats DICOM alternatives

---

### 3. Формат SRM .srm

**Задачи:**
- Изучить документированные части формата
- Найти open-source парсеры
- Интегрировать с Golden Cheetah codebase

**Запросы:**
1. SRM power meter file format specification
2. Golden Cheetah SRM file parser source code
3. SRM training file binary structure documentation
4. Python SRM file reader library
5. Cycling power data file formats comparison

---

### 4. Протоколы передачи данных лактатометров

**Задачи:**
- Lactate Pro 2 Bluetooth protocol
- Lactate Plus serial communication protocol
- Создание Python-библиотеки для live-синхронизации

**Запросы:**
1. Lactate Pro 2 Bluetooth Low Energy protocol specification
2. Lactate Plus serial port communication Python
3. Medical device Bluetooth GATT profiles
4. Real-time lactate data acquisition Python
5. Arkray Lactate Pro SDK API documentation

---

## Ожидаемые результаты

1. Документация по внутренней структуре форматов
2. Python-парсеры для каждого формата
3. Тестовые наборы данных
4. Интеграция в систему VO2max Report

## Риски

- Лицензионные ограничения на реверс-инжиниринг
- Изменение форматов в новых версиях ПО
- Ограниченный доступ к тестовым файлам

---

*План создан: 2025-12-28*
*Приоритет: Высокий (критично для универсальности системы)*
