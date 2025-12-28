# Deep Research: Визуализация физиологических данных (Plotly, Matplotlib)

## Контекст проекта

**VO2max Report** — универсальная система анализа функциональной диагностики спортсменов. Ключевая часть отчётов — графики, показывающие динамику физиологических параметров и маркеры порогов.

### Требования к визуализации

- Графики для отчётов (static images)
- Интерактивные графики для веб-интерфейса
- Типы графиков: линейные, столбчатые, scatter, multi-axis
- Маркеры порогов (АэП, АнП, VO2max)
- Сравнение нескольких тестов

### Что нужно исследовать

1. **Matplotlib vs Plotly**
   - Когда использовать каждый
   - Интеграция с Django

2. **Типы графиков для VO2max**
   - HR vs Power
   - VO2 vs Power
   - Lactate curve
   - Training zones

3. **Интерактивные dashboards**
   - Plotly Dash
   - Bokeh

---

## Сравнение библиотек

### Matplotlib

**Описание:** Основная библиотека для статических графиков в Python

**Преимущества:**
- Максимальный контроль над каждым элементом
- Отличное качество для печати
- Широкая кастомизация
- Встроен во многие научные библиотеки

**Недостатки:**
- Статические графики (без интерактивности)
- Многословный синтаксис

**Когда использовать:**
- Генерация графиков для PDF/DOCX отчётов
- Научные публикации
- Пакетная обработка

### Plotly

**Описание:** Библиотека для интерактивных графиков

**Преимущества:**
- Интерактивность (zoom, pan, hover)
- Красивый дизайн "из коробки"
- Экспорт в статические изображения
- Plotly Dash для dashboards

**Недостатки:**
- Большой размер JS для веба
- Меньше контроля для print

**Когда использовать:**
- Веб-интерфейс приложения
- Exploratory data analysis
- Интерактивные dashboard'ы

---

## Графики для VO2max Report

### 1. HR vs Power (Линейный график)

**Цель:** Показать рост ЧСС при увеличении мощности

**Matplotlib реализация:**
```python
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

def create_hr_power_chart(items, thresholds=None, output_path=None):
    """
    Создаёт график ЧСС vs Мощность.
    
    Args:
        items: QuerySet MeasurementItems
        thresholds: dict с lt1_power, lt2_power
        output_path: путь для сохранения (опционально)
    
    Returns:
        BytesIO с PNG изображением
    """
    # Подготовка данных
    power = [item.power for item in items]
    hr = [item.hr for item in items]
    
    # Создание фигуры
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Основной график
    ax.plot(power, hr, 'o-', color='#e74c3c', linewidth=2, markersize=6, label='ЧСС')
    
    # Заливка зон
    if thresholds:
        lt1 = thresholds.get('lt1_power', min(power))
        lt2 = thresholds.get('lt2_power', max(power))
        
        # Zone 1-2 (до АэП) - зелёный
        ax.axvspan(min(power), lt1, alpha=0.2, color='green', label='Зона 1-2')
        
        # Zone 3 (АэП - АнП) - жёлтый  
        ax.axvspan(lt1, lt2, alpha=0.2, color='yellow', label='Зона 3')
        
        # Zone 4-5 (выше АнП) - красный
        ax.axvspan(lt2, max(power), alpha=0.2, color='red', label='Зона 4-5')
        
        # Вертикальные линии порогов
        ax.axvline(x=lt1, color='green', linestyle='--', linewidth=2, label=f'АэП ({lt1} Вт)')
        ax.axvline(x=lt2, color='orange', linestyle='--', linewidth=2, label=f'АнП ({lt2} Вт)')
    
    # Оформление
    ax.set_xlabel('Мощность (Вт)', fontsize=12)
    ax.set_ylabel('ЧСС (уд/мин)', fontsize=12)
    ax.set_title('Динамика ЧСС при нагрузке', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Границы осей с отступами
    ax.set_xlim(min(power) - 10, max(power) + 10)
    ax.set_ylim(min(hr) - 5, max(hr) + 10)
    
    # Сохранение
    import io
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buffer.seek(0)
    plt.close()
    
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(buffer.getvalue())
        buffer.seek(0)
    
    return buffer
```

---

### 2. VO2 vs Power (Dual-axis график)

**Цель:** Показать динамику VO2 и VCO2 относительно мощности

```python
def create_vo2_power_chart(items, thresholds=None):
    """Создаёт график VO2 и VCO2 vs Мощность."""
    
    power = [item.power for item in items]
    vo2 = [item.vo2_ml_min for item in items]
    vco2 = [item.vco2_ml_min for item in items if item.vco2_ml_min]
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # VO2 на первой оси
    color_vo2 = '#3498db'
    ax1.set_xlabel('Мощность (Вт)', fontsize=12)
    ax1.set_ylabel('VO2 (мл/мин)', color=color_vo2, fontsize=12)
    ax1.plot(power, vo2, 'o-', color=color_vo2, linewidth=2, markersize=6, label='VO2')
    ax1.tick_params(axis='y', labelcolor=color_vo2)
    
    # VCO2 на второй оси
    if vco2:
        ax2 = ax1.twinx()
        color_vco2 = '#e74c3c'
        ax2.set_ylabel('VCO2 (мл/мин)', color=color_vco2, fontsize=12)
        ax2.plot(power[:len(vco2)], vco2, 's-', color=color_vco2, linewidth=2, markersize=6, label='VCO2')
        ax2.tick_params(axis='y', labelcolor=color_vco2)
    
    # Маркер VO2max
    max_vo2_idx = vo2.index(max(vo2))
    ax1.annotate(
        f'VO2max\n{max(vo2):.0f} мл/мин',
        xy=(power[max_vo2_idx], max(vo2)),
        xytext=(power[max_vo2_idx] + 20, max(vo2) + 100),
        arrowprops=dict(arrowstyle='->', color='black'),
        fontsize=10,
        fontweight='bold'
    )
    
    ax1.set_title('Динамика потребления кислорода', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Объединённая легенда
    lines1, labels1 = ax1.get_legend_handles_labels()
    if vco2:
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    else:
        ax1.legend(loc='upper left')
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buffer.seek(0)
    plt.close()
    
    return buffer
```

---

### 3. Lactate Curve (Столбчатая диаграмма)

**Цель:** Показать динамику лактата с выделением порогов

```python
def create_lactate_chart(items, thresholds=None):
    """Создаёт столбчатую диаграмму лактата."""
    
    # Фильтруем только точки с измерением лактата
    lactate_items = [i for i in items if i.lactate is not None]
    
    if not lactate_items:
        return None
    
    power = [item.power for item in lactate_items]
    lactate = [item.lactate for item in lactate_items]
    
    # Определяем цвета столбцов по зонам
    colors = []
    lt1 = thresholds.get('lt1_power', 0) if thresholds else 0
    lt2 = thresholds.get('lt2_power', max(power)) if thresholds else max(power)
    
    for p in power:
        if p <= lt1:
            colors.append('#27ae60')  # Зелёный - зона 1-2
        elif p <= lt2:
            colors.append('#f39c12')  # Жёлтый - зона 3
        else:
            colors.append('#e74c3c')  # Красный - зона 4-5
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(power, lactate, color=colors, edgecolor='black', linewidth=0.5, width=15)
    
    # Значения над столбцами
    for bar, lac in zip(bars, lactate):
        height = bar.get_height()
        ax.annotate(
            f'{lac:.1f}',
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords='offset points',
            ha='center', va='bottom',
            fontsize=9, fontweight='bold'
        )
    
    # Горизонтальные линии референсных значений
    ax.axhline(y=2.0, color='green', linestyle=':', alpha=0.7, label='2 ммоль/л (АэП reference)')
    ax.axhline(y=4.0, color='orange', linestyle=':', alpha=0.7, label='4 ммоль/л (АнП reference)')
    
    ax.set_xlabel('Мощность (Вт)', fontsize=12)
    ax.set_ylabel('Лактат (ммоль/л)', fontsize=12)
    ax.set_title('Динамика лактата крови', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3, axis='y')
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buffer.seek(0)
    plt.close()
    
    return buffer
```

---

### 4. Training Zones Visualization

**Цель:** Визуализация тренировочных зон на основе порогов

```python
def create_training_zones_chart(thresholds, client_hrmax=None):
    """
    Создаёт визуализацию тренировочных зон.
    
    Показывает 5 зон с диапазонами мощности и ЧСС.
    """
    
    lt1_power = thresholds.lt1_power
    lt2_power = thresholds.lt2_power
    max_power = thresholds.power_at_vo2max
    
    lt1_hr = thresholds.lt1_hr
    lt2_hr = thresholds.lt2_hr
    
    # Определение зон
    zones = [
        {'name': 'Зона 1\nВосстановление', 'power_range': (0, lt1_power * 0.55), 
         'hr_range': (0, lt1_hr * 0.65), 'color': '#bdc3c7'},
        {'name': 'Зона 2\nБаза', 'power_range': (lt1_power * 0.55, lt1_power * 0.75), 
         'hr_range': (lt1_hr * 0.65, lt1_hr * 0.80), 'color': '#3498db'},
        {'name': 'Зона 3\nТемпо', 'power_range': (lt1_power * 0.75, lt2_power * 0.90), 
         'hr_range': (lt1_hr * 0.80, lt2_hr * 0.90), 'color': '#2ecc71'},
        {'name': 'Зона 4\nПороговая', 'power_range': (lt2_power * 0.90, lt2_power * 1.05), 
         'hr_range': (lt2_hr * 0.90, lt2_hr * 1.0), 'color': '#f39c12'},
        {'name': 'Зона 5\nВО2макс', 'power_range': (lt2_power * 1.05, max_power), 
         'hr_range': (lt2_hr, client_hrmax), 'color': '#e74c3c'},
    ]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # График мощности
    for i, zone in enumerate(zones):
        width = zone['power_range'][1] - zone['power_range'][0]
        ax1.barh(i, width, left=zone['power_range'][0], color=zone['color'], 
                 edgecolor='black', height=0.6)
        ax1.text(zone['power_range'][0] + width/2, i, zone['name'], 
                 ha='center', va='center', fontsize=9, fontweight='bold')
    
    ax1.set_xlabel('Мощность (Вт)', fontsize=12)
    ax1.set_title('Зоны по мощности', fontsize=14, fontweight='bold')
    ax1.set_yticks([])
    
    # График ЧСС
    for i, zone in enumerate(zones):
        if zone['hr_range'][1] and zone['hr_range'][0]:
            width = zone['hr_range'][1] - zone['hr_range'][0]
            ax2.barh(i, width, left=zone['hr_range'][0], color=zone['color'], 
                     edgecolor='black', height=0.6)
    
    ax2.set_xlabel('ЧСС (уд/мин)', fontsize=12)
    ax2.set_title('Зоны по ЧСС', fontsize=14, fontweight='bold')
    ax2.set_yticks([])
    
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buffer.seek(0)
    plt.close()
    
    return buffer
```

---

### 5. Сравнение нескольких тестов

**Цель:** Показать прогресс спортсмена между тестами

```python
def create_comparison_chart(measurements, parameter='hr'):
    """
    Создаёт график сравнения нескольких тестов.
    
    Args:
        measurements: list of Measurement objects
        parameter: 'hr', 'vo2', 'lactate'
    """
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    colors = plt.cm.viridis(np.linspace(0, 1, len(measurements)))
    
    for i, measurement in enumerate(measurements):
        items = measurement.measurementitems.filter(use_in_report=True).order_by('power')
        
        power = [it.power for it in items]
        values = [getattr(it, parameter) for it in items]
        
        date_str = measurement.date.strftime('%d.%m.%Y')
        ax.plot(power, values, 'o-', color=colors[i], linewidth=2, 
                markersize=6, label=f'Тест {date_str}')
    
    ax.set_xlabel('Мощность (Вт)', fontsize=12)
    
    labels = {
        'hr': 'ЧСС (уд/мин)',
        'vo2_ml_min': 'VO2 (мл/мин)',
        'lactate': 'Лактат (ммоль/л)'
    }
    ax.set_ylabel(labels.get(parameter, parameter), fontsize=12)
    
    ax.set_title(f'Сравнение тестов: {labels.get(parameter, parameter)}', 
                 fontsize=14, fontweight='bold')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buffer.seek(0)
    plt.close()
    
    return buffer
```

---

## Plotly для интерактивных графиков

### Интерактивный HR vs Power

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_interactive_hr_power(items, thresholds=None):
    """Создаёт интерактивный график для веб-интерфейса."""
    
    power = [item.power for item in items]
    hr = [item.hr for item in items]
    time = [item.time_seconds for item in items]
    
    fig = go.Figure()
    
    # Основной trace
    fig.add_trace(go.Scatter(
        x=power,
        y=hr,
        mode='lines+markers',
        name='ЧСС',
        line=dict(color='#e74c3c', width=2),
        marker=dict(size=8),
        hovertemplate='Мощность: %{x} Вт<br>ЧСС: %{y} уд/мин<br>Время: %{text}',
        text=[f'{t//60}:{t%60:02d}' for t in time]
    ))
    
    # Пороги
    if thresholds:
        lt1 = thresholds.get('lt1_power')
        lt2 = thresholds.get('lt2_power')
        
        if lt1:
            fig.add_vline(x=lt1, line_dash='dash', line_color='green',
                          annotation_text=f'АэП: {lt1} Вт')
        if lt2:
            fig.add_vline(x=lt2, line_dash='dash', line_color='orange',
                          annotation_text=f'АнП: {lt2} Вт')
    
    fig.update_layout(
        title='Динамика ЧСС при нагрузке',
        xaxis_title='Мощность (Вт)',
        yaxis_title='ЧСС (уд/мин)',
        template='plotly_white',
        hovermode='x unified'
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')
```

### Dashboard с Plotly Dash

```python
# dashboard.py
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1('VO2max Report Dashboard'),
    
    # Фильтры
    html.Div([
        dcc.Dropdown(
            id='client-dropdown',
            placeholder='Выберите спортсмена'
        ),
        dcc.Dropdown(
            id='measurement-dropdown',
            placeholder='Выберите тестирование'
        ),
    ], style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}),
    
    # Графики
    html.Div([
        dcc.Graph(id='hr-chart', style={'width': '50%'}),
        dcc.Graph(id='vo2-chart', style={'width': '50%'}),
    ], style={'display': 'flex'}),
    
    html.Div([
        dcc.Graph(id='lactate-chart', style={'width': '50%'}),
        dcc.Graph(id='zones-chart', style={'width': '50%'}),
    ], style={'display': 'flex'}),
])

@app.callback(
    [Output('hr-chart', 'figure'),
     Output('vo2-chart', 'figure'),
     Output('lactate-chart', 'figure')],
    [Input('measurement-dropdown', 'value')]
)
def update_charts(measurement_id):
    if not measurement_id:
        return {}, {}, {}
    
    # Загрузка данных
    measurement = Measurement.objects.get(id=measurement_id)
    items = measurement.measurementitems.all()
    
    # Создание графиков
    hr_fig = create_interactive_hr_power(items)
    vo2_fig = create_interactive_vo2(items)
    lactate_fig = create_interactive_lactate(items)
    
    return hr_fig, vo2_fig, lactate_fig

if __name__ == '__main__':
    app.run_server(debug=True)
```

---

## Интеграция с Django

### Matplotlib в Django View

```python
from django.http import HttpResponse

def hr_chart_view(request, measurement_id):
    """View для генерации PNG графика."""
    measurement = get_object_or_404(Measurement, id=measurement_id)
    items = measurement.measurementitems.filter(use_in_report=True)
    
    thresholds = {
        'lt1_power': measurement.thresholds.lt1_power,
        'lt2_power': measurement.thresholds.lt2_power,
    } if hasattr(measurement, 'thresholds') else None
    
    buffer = create_hr_power_chart(items, thresholds)
    
    return HttpResponse(buffer.getvalue(), content_type='image/png')
```

### Plotly в Django Template

```python
# views.py
def measurement_detail(request, measurement_id):
    measurement = get_object_or_404(Measurement, id=measurement_id)
    items = measurement.measurementitems.filter(use_in_report=True)
    
    hr_chart_html = create_interactive_hr_power(items)
    
    return render(request, 'measurement_detail.html', {
        'measurement': measurement,
        'hr_chart': hr_chart_html,
    })
```

```html
<!-- measurement_detail.html -->
{% extends "base.html" %}

{% block content %}
<h1>Тестирование {{ measurement.date }}</h1>

<div class="chart-container">
    {{ hr_chart|safe }}
</div>
{% endblock %}
```

---

## Стилизация и брендирование

### Matplotlib Style

```python
# vo2max_style.mplstyle
# Сохранить в static/styles/

figure.facecolor: white
axes.facecolor: white
axes.edgecolor: #333333
axes.labelcolor: #333333
axes.titlesize: 14
axes.labelsize: 12
axes.titleweight: bold

lines.linewidth: 2
lines.markersize: 6

xtick.color: #333333
ytick.color: #333333

grid.alpha: 0.3

legend.framealpha: 0.8
legend.fontsize: 10

font.family: sans-serif
font.sans-serif: Arial, Helvetica, sans-serif
```

**Применение:**
```python
import matplotlib.pyplot as plt

plt.style.use('static/styles/vo2max_style.mplstyle')
```

---

## Вопросы для дальнейшего исследования

1. **3D визуализации**
   - Power-HR-VO2 surface
   - Time-lapse animations

2. **Export форматы**
   - SVG для масштабирования
   - EMF для Word

3. **Real-time графики**
   - WebSocket для live data
   - Streaming charts

---

## Источники

1. Matplotlib: https://matplotlib.org/stable/
2. Plotly Python: https://plotly.com/python/
3. Plotly Dash: https://dash.plotly.com/
4. Seaborn: https://seaborn.pydata.org/

---

*Документ создан: 2025-12-28*
*Статус: Примеры кода готовы, требуется интеграция*
