# Deep Research: Стандарты данных FIT, TCX, GPX

## Контекст проекта

VO2max Report — система анализа функциональной диагностики, требующая поддержки стандартных спортивных форматов.

## FIT (Flexible and Interoperable Data Transfer)

**Описание:** Бинарный формат Garmin, компактный и богатый данными.

**Python:** `fitparse`
```bash
pip install fitparse
```

```python
from fitparse import FitFile

def parse_fit(file_path):
    fitfile = FitFile(file_path)
    records = []
    for record in fitfile.get_messages('record'):
        records.append({
            'timestamp': record.get_value('timestamp'),
            'hr': record.get_value('heart_rate'),
            'power': record.get_value('power'),
            'cadence': record.get_value('cadence'),
        })
    return records
```

## TCX (Training Center XML)

**Описание:** XML формат Garmin с лапами и trackpoints.

```python
import xml.etree.ElementTree as ET

def parse_tcx(file_path):
    ns = {'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}
    tree = ET.parse(file_path)
    points = []
    for tp in tree.findall('.//tcx:Trackpoint', ns):
        hr = tp.find('tcx:HeartRateBpm/tcx:Value', ns)
        points.append({'hr': int(hr.text) if hr is not None else None})
    return points
```

## GPX (GPS Exchange Format)

**Описание:** Открытый XML для GPS данных.

**Python:** `gpxpy`
```bash
pip install gpxpy
```

```python
import gpxpy

def parse_gpx(file_path):
    with open(file_path) as f:
        gpx = gpxpy.parse(f)
    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append({
                    'time': point.time,
                    'lat': point.latitude,
                    'lon': point.longitude,
                })
    return points
```

## Сравнение

| Формат | Тип | HR | Power | GPS | Размер |
|--------|-----|-----|-------|-----|--------|
| FIT | Binary | ✅ | ✅ | ✅ | Маленький |
| TCX | XML | ✅ | ✅ | ✅ | Средний |
| GPX | XML | ⚠️ | ❌ | ✅ | Большой |

## Рекомендация

- **Импорт:** Поддержка всех трёх форматов
- **Экспорт:** FIT для совместимости с Strava/Garmin

---
*Документ создан: 2025-12-28*
