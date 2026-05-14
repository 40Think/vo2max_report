# Deep Research: Форматы данных газоанализаторов и метаболических систем

## Контекст проекта

**VO2max Report** — универсальная система анализа функциональной диагностики спортсменов. Мы создаём Python/Django приложение, которое должно импортировать данные с ЛЮБОГО оборудования для метаболического тестирования, не привязываясь к конкретному производителю.

### Проблема

Каждый производитель газоанализаторов использует свой проприетарный формат данных:
- COSMED → OMNIA software → .xpo, .txt, .xls
- Cortex MetaMax → MetaSoft Studio → .msstest
- VO2 Master → CSV / API
- PNOE → CSV с уникальной структурой
- Garmin / Polar / Suunto → FIT, TCX, GPX
- Самодельные системы → JSON, CSV с произвольными колонками

### Что нужно исследовать

1. **Детальная структура форматов файлов**
   - Какие колонки/поля присутствуют в каждом формате?
   - Какие единицы измерения используются (мл/мин vs л/мин, bpm vs Hz)?
   - Какие разделители и локализации (запятая vs точка для десятичных)?

2. **Официальные SDK и API производителей**
   - Есть ли открытые API для COSMED OMNIA?
   - Как работает MetaSoft Studio export?
   - Garmin Health API — условия доступа для малого бизнеса
   - VO2 Master API документация

3. **Библиотеки Python для парсинга**
   - fitparse для FIT файлов
   - gpxpy для GPX
   - lxml для TCX (XML)
   - pandas для CSV с различными настройками

4. **Маппинг полей между форматами**
   - Как нормализовать VO2 из разных источников?
   - Стандартизация временных меток
   - Обработка пропущенных данных

5. **Проприетарные бинарные форматы**
   - Как реверс-инжинирить .pc2, .msstest?
   - Какие открытые проекты занимались декодированием?

---

## Найденная информация

### COSMED

**Оборудование:** K5 (портативный), Quark CPET (лабораторный)

**Программное обеспечение:** OMNIA

**Форматы экспорта:**
- `.xpo` — проприетарный формат COSMED
- `.txt` (ASCII) — текстовый табличный формат
- `.xls` — Microsoft Excel (Quark b2 и старше)

**Типичные поля:**
- Time, VO2 (mL/min), VCO2, RER, VE, HR, Rf, Tv
- Возможны расширенные метрики: SpO2, FeO2, FeCO2

**Важно:** COSMED часто использует запятую как десятичный разделитель в европейских локализациях.

---

### Cortex MetaMax

**Оборудование:** MetaMax 3B, MetaMax 3C

**Программное обеспечение:** MetaSoft Studio

**Форматы:**
- `.msstest` — проприетарный формат MetaSoft Studio
- CSV export возможен через меню программы

**Особенности:**
- Данные передаются по Bluetooth на ПК
- MetaSoft Studio — центральное ПО для всех систем Cortex
- Вероятно поддерживает CSV export для совместимости

**Типичные поля (предполагаемые):**
- Zeit (время), VO2, VCO2, RQ, VE, BF (Rf), VT (Tv), HR

---

### PNOE

**Оборудование:** PNOE portable metabolic analyzer

**Формат:** CSV с точкой с запятой (`;`) как разделитель

**Структура файла (пример из проекта):**
```csv
T(sec);PHASE;HR(bpm);VO2(ml/min);VCO2(ml/min);RER;VE(l/min);FEO2;FECO2;...
0;;144.83;2517.60;2277.98;0.90;82.35;0.1746;0.0319;...
```

**Особенности:**
- Десятичный разделитель — точка
- Поле PHASE может быть пустым
- Включает FEO2, FECO2 (фракции газов)

---

### Garmin FIT Format

**Описание:** Flexible and Interoperable Data Transfer — бинарный формат Garmin

**Библиотека Python:** `fitparse`

**Содержимое:**
- GPS координаты, время
- Heart Rate, Speed, Distance, Power, Cadence
- Lap data, Device info
- Workout instructions (для структурированных тренировок)

**Преимущества:**
- Самый компактный формат
- Поддерживается большинством платформ (Strava, TrainingPeaks)

**Ограничения:**
- Бинарный — не читаемый без парсера
- Проприетарный Garmin, но хорошо документирован

---

### TCX (Training Center XML)

**Описание:** XML формат Garmin (2008)

**Библиотека Python:** `lxml`, `xml.etree`, специализированные пакеты

**Структура:**
```xml
<TrainingCenterDatabase>
  <Activities>
    <Activity Sport="Biking">
      <Lap StartTime="...">
        <Track>
          <Trackpoint>
            <Time>2024-01-01T10:00:00Z</Time>
            <Position><LatitudeDegrees>...</LatitudeDegrees></Position>
            <HeartRateBpm><Value>150</Value></HeartRateBpm>
            <Cadence>90</Cadence>
            <Extensions>
              <ns3:TPX><ns3:Watts>200</ns3:Watts></ns3:TPX>
            </Extensions>
          </Trackpoint>
        </Track>
      </Lap>
    </Activity>
  </Activities>
</TrainingCenterDatabase>
```

**Содержимое:**
- Activity metadata, Laps, Trackpoints
- HR, Cadence, Power (через Extensions)
- GPS coordinates

---

### GPX (GPS Exchange Format)

**Описание:** Открытый XML формат для GPS данных

**Библиотека Python:** `gpxpy`

**Основные элементы:**
- Waypoints — точки интереса
- Tracks — записанные треки (массив точек)
- Routes — запланированные маршруты

**Ограничения для VO2max:**
- Фокус на географии, минимум физиологических данных
- HR и другие метрики могут храниться в Extensions

---

## Python библиотеки для парсинга

| Библиотека | Формат | Пример использования |
|------------|--------|---------------------|
| `fitparse` | FIT | `FitFile('activity.fit')` |
| `gpxpy` | GPX | `gpxpy.parse(open('track.gpx'))` |
| `lxml` / `BeautifulSoup` | TCX, XML | `etree.parse('activity.tcx')` |
| `pandas` | CSV | `pd.read_csv('data.csv', sep=';', decimal=',')` |

---

## Стратегия унификации данных

### Каноническая модель данных

Все форматы должны конвертироваться в единую структуру:

```python
class UnifiedMeasurementItem:
    timestamp: datetime          # Абсолютное время точки
    time_seconds: float          # Время от начала теста, сек
    
    # Метаболические параметры
    vo2_ml_min: float            # Потребление O2, мл/мин
    vo2_ml_kg_min: float         # Относительное VO2, мл/кг/мин (если известен вес)
    vco2_ml_min: float           # Выделение CO2, мл/мин
    rer: float                   # Дыхательный коэффициент
    
    # Вентиляционные параметры
    ve_l_min: float              # Минутная вентиляция, л/мин
    rf: int                      # Частота дыхания, вдохов/мин
    tv_l: float                  # Дыхательный объём, л
    
    # Кардио
    hr: int                      # ЧСС, уд/мин
    
    # Нагрузка
    power_watts: float           # Мощность, Вт
    cadence: int                 # Каденс, об/мин
    speed_kmh: float             # Скорость, км/ч
    
    # Дополнительно
    lactate_mmol: float          # Лактат, ммоль/л (ручной ввод)
    feo2: float                  # Концентрация O2 в выдохе, %
    feco2: float                 # Концентрация CO2 в выдохе, %
```

### Архитектура парсеров

```
          ┌──────────────────────────────────────────┐
          │           BaseParser (ABC)               │
          │  - can_parse(file_path) -> bool          │
          │  - parse(file_path) -> Measurement       │
          └────────────────┬─────────────────────────┘
                           │
     ┌─────────────────────┼─────────────────────┐
     │                     │                     │
┌────┴────┐          ┌─────┴─────┐         ┌────┴────┐
│CSVParser│          │FITParser  │         │XMLParser│
│(Ergospiro│         │(Garmin)   │         │(TCX/GPX)│
│ PNOE)   │          └───────────┘         └─────────┘
└─────────┘
```

---

## Вопросы для дальнейшего исследования

1. **COSMED OMNIA API**
   - Есть ли REST API или SDK для интеграции?
   - Можно ли программно экспортировать данные?

2. **Cortex MetaSoft Studio**
   - Формат .msstest — это SQLite, XML или бинарный?
   - Есть ли документация по структуре файла?

3. **VO2 Master**
   - Как работает их облачная платформа?
   - Есть ли API для получения raw data?

4. **Лактатометры (Lactate Pro, Lactate Plus)**
   - Как вводить данные лактата — ручной ввод или есть экспорт?
   - Синхронизация по времени с газоанализатором

5. **Эргометры (Wattbike, Cyclus2, SRM)**
   - Какие форматы экспорта поддерживают?
   - Интеграция с ANT+ / Bluetooth протоколами

---

## Источники и ссылки для изучения

1. **FIT SDK:** https://developer.garmin.com/fit/
2. **fitparse (Python):** https://github.com/dtcooper/python-fitparse
3. **gpxpy:** https://github.com/tkrajina/gpxpy
4. **COSMED Technical:** https://www.cosmed.com/
5. **Cortex Medical:** https://www.cortex-medical.com/
6. **VO2 Master:** https://vo2master.com/
7. **TCX Schema:** https://www8.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd

---

## Рекомендации для реализации

1. **Начать с CSV парсеров** — наиболее распространённый формат экспорта
2. **Добавить FIT парсер** — для интеграции с Garmin и другими устройствами
3. **Реализовать автодетекцию формата** — по расширению и содержимому файла
4. **Создать UI для маппинга колонок** — если формат неизвестен, пользователь указывает соответствия
5. **Логировать все импорты** — для отладки и аудита

---

*Документ создан: 2025-12-28*
*Статус: Требует дополнительного исследования по API производителей*
