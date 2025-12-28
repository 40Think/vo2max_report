# Deep Research: Генерация отчётов в Python (DOCX, PDF)

## Контекст проекта

**VO2max Report** — универсальная система анализа функциональной диагностики спортсменов. Ключевая функция — генерация профессиональных отчётов с графиками, таблицами и маркерами физиологических порогов.

### Требования к отчётам

- Формат: DOCX (редактируемый), PDF (финальный)
- Содержание: данные спортсмена, таблицы измерений, графики, рекомендации
- Шаблонизация: возможность кастомизации под разные лаборатории
- Графики: HR, VO2, Power, Lactate curves с маркерами порогов

### Что нужно исследовать

1. **Библиотеки для работы с DOCX**
   - python-docx
   - python-docx-template
   - docxtpl

2. **Генерация PDF**
   - WeasyPrint
   - ReportLab
   - FPDF
   - Конвертация DOCX → PDF

3. **Встраивание графиков**
   - Matplotlib → Image → DOCX
   - Plotly → Static image
   - Native charts (Xceed alternative)

4. **Шаблонизация отчётов**
   - Jinja2 templates
   - Bookmarks/Placeholders

---

## Библиотеки для работы с DOCX

### 1. python-docx

**GitHub:** https://github.com/python-openxml/python-docx

**Описание:** Основная библиотека для создания и редактирования .docx файлов

**Установка:**
```bash
pip install python-docx
```

**Возможности:**
- Создание документов с нуля
- Добавление параграфов, заголовков
- Создание и форматирование таблиц
- Вставка изображений
- Работа со стилями

**Пример создания документа:**
```python
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

# Создание документа
doc = Document()

# Заголовок
title = doc.add_heading('Отчёт о функциональном тестировании', level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Параграф
doc.add_paragraph('Дата тестирования: 28.12.2024')

# Таблица данных спортсмена
table = doc.add_table(rows=4, cols=2)
table.style = 'Table Grid'

cells = [
    ('ФИО:', 'Иванов Иван Иванович'),
    ('Дата рождения:', '15.05.1990'),
    ('Рост:', '180 см'),
    ('Вес:', '75 кг'),
]

for i, (label, value) in enumerate(cells):
    table.rows[i].cells[0].text = label
    table.rows[i].cells[1].text = value

# Вставка изображения (график)
doc.add_heading('Динамика ЧСС', level=1)
doc.add_picture('hr_chart.png', width=Inches(6))

# Сохранение
doc.save('report.docx')
```

**Работа с таблицами:**
```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_cell_shading(cell, fill_color):
    """Установить цвет фона ячейки."""
    shading_elm = OxmlElement('w:shd')
    shading_elm.set(qn('w:fill'), fill_color)
    cell._tc.get_or_add_tcPr().append(shading_elm)

# Создание таблицы измерений
table = doc.add_table(rows=1, cols=7)
table.style = 'Table Grid'

# Заголовки
headers = ['Время', 'Мощность', 'ЧСС', 'VO2', 'Ve', 'Лактат', 'Порог']
header_cells = table.rows[0].cells
for i, header in enumerate(headers):
    header_cells[i].text = header
    set_cell_shading(header_cells[i], 'D9E2F3')

# Данные
for item in measurement_items:
    row = table.add_row()
    row.cells[0].text = str(item.time_seconds)
    row.cells[1].text = str(item.power)
    row.cells[2].text = str(item.hr)
    row.cells[3].text = f'{item.vo2_ml_min:.0f}'
    row.cells[4].text = f'{item.ve:.1f}'
    row.cells[5].text = f'{item.lactate:.1f}' if item.lactate else '-'
    row.cells[6].text = item.sport_parameter or ''
    
    # Подсветка порогов
    if item.sport_parameter == 'anp':
        for cell in row.cells:
            set_cell_shading(cell, 'FFE699')  # Жёлтый
```

---

### 2. python-docx-template (docxtpl)

**GitHub:** https://github.com/elapouya/python-docx-template

**Описание:** Jinja2 шаблонизатор для Word документов

**Установка:**
```bash
pip install docxtpl
```

**Преимущества:**
- Создание шаблонов в Word с плейсхолдерами
- Jinja2 синтаксис (циклы, условия, фильтры)
- Удобно для сложных отчётов с фиксированным layout

**Создание шаблона (в Word):**
```
ОТЧЁТ О ФУНКЦИОНАЛЬНОМ ТЕСТИРОВАНИИ

Спортсмен: {{ client.full_name }}
Дата: {{ measurement.date|format_date }}
Вес: {{ client.weight }} кг

{% for item in items %}
    {{ item.time }} | {{ item.power }} Вт | {{ item.hr }} уд/мин
{% endfor %}

VO2max: {{ vo2max }} мл/кг/мин
```

**Python генерация:**
```python
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm

# Загрузка шаблона
doc = DocxTemplate('report_template.docx')

# Подготовка данных
context = {
    'client': {
        'full_name': 'Иванов Иван Иванович',
        'weight': 75,
    },
    'measurement': {
        'date': datetime.now(),
    },
    'items': [
        {'time': '00:03:00', 'power': 100, 'hr': 120},
        {'time': '00:06:00', 'power': 150, 'hr': 135},
        {'time': '00:09:00', 'power': 200, 'hr': 155},
    ],
    'vo2max': 55.3,
    # Изображение графика
    'hr_chart': InlineImage(doc, 'hr_chart.png', width=Mm(150)),
}

# Рендеринг
doc.render(context)
doc.save('report_filled.docx')
```

**Таблицы в шаблоне:**
```
| Время | Мощность | ЧСС | VO2 |
|-------|----------|-----|-----|
{%tr for item in items %}
| {{ item.time }} | {{ item.power }} | {{ item.hr }} | {{ item.vo2 }} |
{%tr endfor %}
```

---

### 3. Сравнение подходов

| Критерий | python-docx | docxtpl |
|----------|-------------|---------|
| Гибкость | Максимальная (programmatic) | Средняя (шаблоны) |
| Простота | Сложнее для layout | Проще для повторяющихся отчётов |
| Изменение layout | Код | Редактирование Word файла |
| Кастомизация | Полная | Ограничена Jinja2 |
| Производительность | Быстрее | Медленнее (парсинг шаблона) |

**Рекомендация:** Использовать **docxtpl** для стандартных отчётов с шаблонами, **python-docx** для программной генерации сложных элементов (графики, таблицы с условным форматированием).

---

## Генерация PDF

### 1. WeasyPrint

**Описание:** Конвертация HTML/CSS в PDF

**Установка:**
```bash
pip install weasyprint
```

**Преимущества:**
- Использует стандартный HTML/CSS
- Поддержка CSS Paged Media
- Хорошее качество типографики

**Пример:**
```python
from weasyprint import HTML, CSS

html_content = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
        h1 { color: #333; text-align: center; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; }
        th { background-color: #007bff; color: white; }
        .threshold { background-color: #ffe699; }
    </style>
</head>
<body>
    <h1>Отчёт о функциональном тестировании</h1>
    <p>Спортсмен: Иванов Иван Иванович</p>
    
    <table>
        <tr>
            <th>Время</th>
            <th>Мощность</th>
            <th>ЧСС</th>
            <th>VO2</th>
        </tr>
        <tr>
            <td>00:03:00</td>
            <td>100 Вт</td>
            <td>120</td>
            <td>25.3</td>
        </tr>
        <tr class="threshold">
            <td>00:09:00</td>
            <td>200 Вт</td>
            <td>155</td>
            <td>42.1</td>
        </tr>
    </table>
    
    <img src="hr_chart.png" style="width: 100%;">
</body>
</html>
"""

# Генерация PDF
HTML(string=html_content).write_pdf('report.pdf')
```

**Интеграция с Django:**
```python
from django.template.loader import render_to_string
from weasyprint import HTML

def generate_pdf_report(request, measurement_id):
    measurement = Measurement.objects.get(id=measurement_id)
    
    html_string = render_to_string('reports/pdf_template.html', {
        'measurement': measurement,
        'items': measurement.measurementitems.all(),
    })
    
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_{measurement_id}.pdf"'
    return response
```

---

### 2. ReportLab

**Описание:** Низкоуровневая библиотека для создания PDF

**Установка:**
```bash
pip install reportlab
```

**Преимущества:**
- Полный контроль над layout
- Высокая производительность
- Поддержка сложной графики

**Пример:**
```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Создание документа
doc = SimpleDocTemplate('report.pdf', pagesize=A4)
styles = getSampleStyleSheet()
elements = []

# Заголовок
title_style = ParagraphStyle(
    'Title',
    parent=styles['Title'],
    fontSize=18,
    spaceAfter=30
)
elements.append(Paragraph('Отчёт о функциональном тестировании', title_style))

# Таблица
data = [
    ['Время', 'Мощность', 'ЧСС', 'VO2'],
    ['00:03:00', '100 Вт', '120', '25.3'],
    ['00:06:00', '150 Вт', '135', '35.2'],
    ['00:09:00', '200 Вт', '155', '42.1'],
]

table = Table(data, colWidths=[3*cm, 3*cm, 2*cm, 2*cm])
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#ffe699')),  # Порог
]))
elements.append(table)

# Изображение графика
elements.append(Image('hr_chart.png', width=15*cm, height=8*cm))

# Сборка документа
doc.build(elements)
```

---

### 3. Конвертация DOCX → PDF

**Вариант 1: LibreOffice (headless)**
```bash
libreoffice --headless --convert-to pdf report.docx
```

**Python wrapper:**
```python
import subprocess

def convert_docx_to_pdf(docx_path, output_dir):
    subprocess.run([
        'libreoffice',
        '--headless',
        '--convert-to', 'pdf',
        '--outdir', output_dir,
        docx_path
    ], check=True)
```

**Вариант 2: docx2pdf (Windows/macOS)**
```bash
pip install docx2pdf
```

```python
from docx2pdf import convert

convert('report.docx', 'report.pdf')
```

---

## Встраивание графиков

### Matplotlib → Image → DOCX

```python
import matplotlib.pyplot as plt
import io
from docx.shared import Inches

def create_hr_chart(measurement_items):
    """Создаёт график ЧСС и возвращает BytesIO."""
    times = [item.time_seconds / 60 for item in measurement_items]  # минуты
    hr_values = [item.hr for item in measurement_items]
    power_values = [item.power for item in measurement_items]
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # ЧСС
    ax1.set_xlabel('Время (мин)')
    ax1.set_ylabel('ЧСС (уд/мин)', color='red')
    ax1.plot(times, hr_values, 'r-', linewidth=2, label='ЧСС')
    ax1.tick_params(axis='y', labelcolor='red')
    
    # Мощность (второй Y-axis)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Мощность (Вт)', color='blue')
    ax2.plot(times, power_values, 'b-', linewidth=2, label='Мощность')
    ax2.tick_params(axis='y', labelcolor='blue')
    
    # Маркеры порогов
    for item in measurement_items:
        if item.sport_parameter == 'aep':
            ax1.axvline(x=item.time_seconds/60, color='green', linestyle='--', label='АэП')
        elif item.sport_parameter == 'anp':
            ax1.axvline(x=item.time_seconds/60, color='orange', linestyle='--', label='АнП')
    
    plt.title('Динамика ЧСС и мощности')
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper left')
    
    # Сохранение в BytesIO
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    return buffer

# Использование в docx
doc = Document()
chart_buffer = create_hr_chart(measurement_items)
doc.add_picture(chart_buffer, width=Inches(6))
```

### Plotly → Static Image

```python
import plotly.graph_objects as go
import plotly.io as pio

def create_lactate_chart(items):
    """Создаёт столбчатую диаграмму лактата."""
    power_values = [item.power for item in items if item.lactate]
    lactate_values = [item.lactate for item in items if item.lactate]
    
    fig = go.Figure(data=[
        go.Bar(
            x=power_values,
            y=lactate_values,
            marker_color=['yellow' if i.sport_parameter else 'steelblue' for i in items if i.lactate],
            text=[f'{l:.1f}' for l in lactate_values],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title='Динамика лактата',
        xaxis_title='Мощность (Вт)',
        yaxis_title='Лактат (ммоль/л)',
        template='plotly_white'
    )
    
    # Сохранение как image
    img_bytes = pio.to_image(fig, format='png', width=800, height=500, scale=2)
    return io.BytesIO(img_bytes)
```

---

## Архитектура генерации отчётов в VO2max Report

### Сервис генерации отчётов

```python
from abc import ABC, abstractmethod

class BaseReportGenerator(ABC):
    """Базовый класс генератора отчётов."""
    
    @abstractmethod
    def generate(self, measurement, format: str) -> bytes:
        pass

class DocxReportGenerator(BaseReportGenerator):
    """Генератор DOCX отчётов."""
    
    def __init__(self, template_path: str = None):
        self.template_path = template_path or 'templates/default_report.docx'
    
    def generate(self, measurement, format='docx') -> bytes:
        from docxtpl import DocxTemplate, InlineImage
        
        doc = DocxTemplate(self.template_path)
        
        # Генерация графиков
        hr_chart = self._create_hr_chart(measurement)
        lactate_chart = self._create_lactate_chart(measurement)
        
        context = {
            'client': measurement.client,
            'measurement': measurement,
            'items': measurement.measurementitems.filter(use_in_report=True),
            'thresholds': measurement.thresholds,
            'hr_chart': InlineImage(doc, hr_chart),
            'lactate_chart': InlineImage(doc, lactate_chart),
        }
        
        doc.render(context)
        
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        if format == 'pdf':
            return self._convert_to_pdf(buffer)
        return buffer.getvalue()
    
    def _create_hr_chart(self, measurement):
        # ... matplotlib код ...
        pass
    
    def _convert_to_pdf(self, docx_buffer):
        # Сохранить временный файл и конвертировать через LibreOffice
        pass
```

### Django View

```python
from django.http import HttpResponse, FileResponse

def download_report(request, measurement_id):
    measurement = get_object_or_404(Measurement, id=measurement_id)
    format = request.GET.get('format', 'docx')
    
    generator = DocxReportGenerator()
    report_bytes = generator.generate(measurement, format=format)
    
    content_type = 'application/pdf' if format == 'pdf' else \
                   'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    
    response = HttpResponse(report_bytes, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="report_{measurement_id}.{format}"'
    return response
```

---

## Вопросы для дальнейшего исследования

1. **Шаблоны для разных типов отчётов**
   - Стандартный VO2max отчёт
   - Сокращённый отчёт для спортсмена
   - Детализированный отчёт для врача

2. **Брендирование**
   - Логотипы лабораторий
   - Цветовые схемы
   - Шрифты

3. **Локализация**
   - Мультиязычные отчёты
   - Форматы чисел и дат

4. **Производительность**
   - Асинхронная генерация для больших отчётов
   - Кэширование графиков

---

## Источники

1. python-docx documentation: https://python-docx.readthedocs.io/
2. python-docx-template: https://docxtpl.readthedocs.io/
3. WeasyPrint: https://weasyprint.org/
4. ReportLab: https://www.reportlab.com/
5. Matplotlib: https://matplotlib.org/
6. Plotly: https://plotly.com/python/

---

*Документ создан: 2025-12-28*
*Статус: Технические решения определены, требуется имплементация*
