# Deep Research: Алгоритмы расчёта физиологических порогов

## Контекст проекта

**VO2max Report** — универсальная система анализа функциональной диагностики спортсменов. Ключевой функционал — автоматическое определение и визуализация физиологических порогов (LT1/VT1, LT2/VT2, VO2max) для построения тренировочных зон.

### Почему это важно

- Пороги определяют границы тренировочных зон
- Автоматическое определение экономит время специалиста
- Стандартизация методов повышает воспроизводимость результатов

### Что нужно исследовать

1. **Методы определения лактатных порогов (LT1, LT2)**
   - OBLA (Onset of Blood Lactate Accumulation)
   - Dmax method
   - Log-log method
   - Individual anaerobic threshold (IAT)

2. **Методы определения вентиляционных порогов (VT1, VT2)**
   - V-slope method
   - Ventilatory equivalents method
   - Excess CO2 method

3. **Новые методы на основе HRV**
   - DFA alpha-1
   - Kubios algorithm

4. **Алгоритмы для программной реализации**

---

## Лактатные пороги (LT1, LT2)

### Терминология

| Термин | Другие названия | Описание |
|--------|-----------------|----------|
| **LT1** | Aerobic Threshold, Lactate Threshold 1 | Первое увеличение лактата над базовым уровнем |
| **LT2** | Anaerobic Threshold, MLSS, OBLA | Максимальный стабильный уровень лактата |

### Физиологическое значение

**LT1 (Аэробный порог):**
- Лактат начинает накапливаться (~2 ммоль/л)
- Переход от преимущественно жирового к смешанному метаболизму
- Соответствует верхней границе Zone 2 (зона базовой выносливости)

**LT2 (Анаэробный порог):**
- Лактат накапливается экспоненциально (~4 ммоль/л)
- Максимальная интенсивность для длительной работы
- Функциональный порог мощности (FTP) ≈ LT2

---

### Методы определения LT1

#### 1. Baseline Plus Method (Bsln+)

**Описание:** LT1 = интенсивность, при которой лактат увеличился на 0.5-1.0 ммоль/л над базовым уровнем.

**Алгоритм:**
```python
def find_lt1_baseline_plus(power_values, lactate_values, delta=0.5):
    """
    Находит LT1 методом Baseline Plus.
    
    Args:
        power_values: список мощностей (Вт)
        lactate_values: соответствующие значения лактата (ммоль/л)
        delta: порог увеличения над базовым (по умолчанию 0.5)
    
    Returns:
        power_at_lt1: мощность на LT1
    """
    baseline = lactate_values[0]  # Лактат покоя или на минимальной нагрузке
    threshold = baseline + delta
    
    for i, lactate in enumerate(lactate_values):
        if lactate >= threshold:
            # Линейная интерполяция
            if i > 0:
                prev_lac = lactate_values[i-1]
                prev_power = power_values[i-1]
                curr_power = power_values[i]
                
                # Интерполяция
                ratio = (threshold - prev_lac) / (lactate - prev_lac)
                power_at_lt1 = prev_power + ratio * (curr_power - prev_power)
                return power_at_lt1
            return power_values[i]
    
    return None  # LT1 не достигнут
```

---

#### 2. Log-Log Method

**Описание:** Лактат и мощность логарифмируются, строится регрессия, находится точка перелома.

**Алгоритм:**
```python
import numpy as np
from scipy.optimize import curve_fit

def find_lt1_loglog(power_values, lactate_values):
    """
    Находит LT1 методом Log-Log.
    
    Строит log(lactate) vs log(power), находит breakpoint.
    """
    log_power = np.log(power_values)
    log_lactate = np.log(lactate_values)
    
    # Segmented regression - ищем точку перелома
    best_breakpoint = None
    best_residual = float('inf')
    
    for bp_idx in range(2, len(power_values) - 2):
        # Fit two lines
        x1, y1 = log_power[:bp_idx], log_lactate[:bp_idx]
        x2, y2 = log_power[bp_idx:], log_lactate[bp_idx:]
        
        slope1, intercept1 = np.polyfit(x1, y1, 1)
        slope2, intercept2 = np.polyfit(x2, y2, 1)
        
        # Calculate residuals
        pred1 = slope1 * x1 + intercept1
        pred2 = slope2 * x2 + intercept2
        
        residual = np.sum((y1 - pred1)**2) + np.sum((y2 - pred2)**2)
        
        if residual < best_residual:
            best_residual = residual
            best_breakpoint = bp_idx
    
    power_at_lt1 = power_values[best_breakpoint]
    return power_at_lt1
```

---

### Методы определения LT2

#### 1. Fixed Lactate Values (OBLA)

**Описание:** LT2 = мощность при лактате 4.0 ммоль/л (Onset of Blood Lactate Accumulation).

**Внимание:** Метод OBLA критикуется за игнорирование индивидуальных различий.

**Алгоритм:**
```python
from scipy.interpolate import interp1d

def find_lt2_obla(power_values, lactate_values, obla_threshold=4.0):
    """
    Находит LT2 методом OBLA (фиксированный порог).
    
    Args:
        obla_threshold: порог лактата (по умолчанию 4.0 ммоль/л)
    """
    # Интерполяция
    f = interp1d(lactate_values, power_values, kind='linear', fill_value='extrapolate')
    power_at_lt2 = f(obla_threshold)
    
    return float(power_at_lt2)
```

---

#### 2. Dmax Method

**Описание:** LT2 = точка на лактатной кривой, максимально удалённая от линии, соединяющей первую и последнюю точки.

**Алгоритм:**
```python
import numpy as np

def find_lt2_dmax(power_values, lactate_values):
    """
    Находит LT2 методом Dmax.
    
    Строит линию между первой и последней точкой,
    находит точку кривой с максимальным расстоянием до этой линии.
    """
    power = np.array(power_values)
    lactate = np.array(lactate_values)
    
    # Полиномиальная регрессия для сглаживания
    coeffs = np.polyfit(power, lactate, 3)
    poly = np.poly1d(coeffs)
    
    # Линия от первой до последней точки
    x0, y0 = power[0], lactate[0]
    x1, y1 = power[-1], lactate[-1]
    
    # Генерируем много точек на кривой
    power_fine = np.linspace(power[0], power[-1], 1000)
    lactate_fitted = poly(power_fine)
    
    # Расстояние от точки до линии
    # Линия: (y1-y0)*x - (x1-x0)*y + x1*y0 - y1*x0 = 0
    # Расстояние = |Ax + By + C| / sqrt(A^2 + B^2)
    A = y1 - y0
    B = -(x1 - x0)
    C = x1 * y0 - y1 * x0
    
    distances = np.abs(A * power_fine + B * lactate_fitted + C) / np.sqrt(A**2 + B**2)
    
    max_idx = np.argmax(distances)
    power_at_lt2 = power_fine[max_idx]
    
    return power_at_lt2
```

---

#### 3. Individual Anaerobic Threshold (IAT) / Lactate Minimum Test

**Описание:** Более точный индивидуальный метод, но требует специального протокола тестирования.

---

## Вентиляционные пороги (VT1, VT2)

### Преимущества перед лактатными порогами

- Неинвазивный метод (без забора крови)
- Может определяться по данным газоанализатора непрерывно
- Высокая корреляция с LT1/LT2 (r = 0.9+)

---

### Методы определения VT1

#### 1. V-Slope Method

**Описание:** VT1 = точка, где наклон VCO2 vs VO2 превышает 1.0.

**Физиология:** До VT1 RER < 1.0, после VT1 — VCO2 растёт быстрее VO2 из-за буферизации CO2.

**Алгоритм:**
```python
import numpy as np
from scipy.optimize import curve_fit

def find_vt1_vslope(vo2_values, vco2_values, power_values):
    """
    Находит VT1 методом V-Slope.
    
    Строит VCO2 vs VO2, находит точку перелома наклона.
    """
    vo2 = np.array(vo2_values)
    vco2 = np.array(vco2_values)
    power = np.array(power_values)
    
    best_breakpoint = None
    best_residual = float('inf')
    
    for bp_idx in range(5, len(vo2) - 5):
        # Первый сегмент: наклон < 1
        x1, y1 = vo2[:bp_idx], vco2[:bp_idx]
        # Второй сегмент: наклон > 1
        x2, y2 = vo2[bp_idx:], vco2[bp_idx:]
        
        slope1, intercept1 = np.polyfit(x1, y1, 1)
        slope2, intercept2 = np.polyfit(x2, y2, 1)
        
        # Критерий: slope1 < 1, slope2 > 1
        if slope1 < 1.0 and slope2 > 1.0:
            pred1 = slope1 * x1 + intercept1
            pred2 = slope2 * x2 + intercept2
            
            residual = np.sum((y1 - pred1)**2) + np.sum((y2 - pred2)**2)
            
            if residual < best_residual:
                best_residual = residual
                best_breakpoint = bp_idx
    
    if best_breakpoint:
        return power[best_breakpoint]
    return None
```

---

#### 2. Ventilatory Equivalents Method

**Описание:** VT1 = точка, где VE/VO2 начинает расти, а VE/VCO2 остаётся стабильным.

**Алгоритм:**
```python
def find_vt1_ventilatory_equivalents(ve_values, vo2_values, vco2_values, power_values):
    """
    Находит VT1 по вентиляторным эквивалентам.
    
    VT1: VE/VO2 растёт, VE/VCO2 стабилен или снижается.
    """
    ve_vo2 = np.array(ve_values) / np.array(vo2_values)
    ve_vco2 = np.array(ve_values) / np.array(vco2_values)
    power = np.array(power_values)
    
    # Находим точку, где VE/VO2 начинает расти
    # Используем скользящее окно для сглаживания
    window = 3
    
    for i in range(window, len(ve_vo2) - window):
        # Среднее до точки
        before_vo2 = np.mean(ve_vo2[i-window:i])
        after_vo2 = np.mean(ve_vo2[i:i+window])
        
        before_vco2 = np.mean(ve_vco2[i-window:i])
        after_vco2 = np.mean(ve_vco2[i:i+window])
        
        # VE/VO2 растёт, VE/VCO2 стабилен
        vo2_increase = after_vo2 > before_vo2 * 1.05
        vco2_stable = abs(after_vco2 - before_vco2) / before_vco2 < 0.05
        
        if vo2_increase and vco2_stable:
            return power[i]
    
    return None
```

---

### Методы определения VT2 (Respiratory Compensation Point)

#### 1. VE/VCO2 Inflection

**Описание:** VT2 = точка, где VE/VCO2 также начинает расти (оба эквивалента растут).

**Алгоритм:**
```python
def find_vt2_rcp(ve_values, vo2_values, vco2_values, power_values):
    """
    Находит VT2 (Respiratory Compensation Point).
    
    VT2: И VE/VO2, и VE/VCO2 растут одновременно.
    """
    ve_vo2 = np.array(ve_values) / np.array(vo2_values)
    ve_vco2 = np.array(ve_values) / np.array(vco2_values)
    power = np.array(power_values)
    
    window = 3
    
    for i in range(window, len(ve_vo2) - window):
        before_vo2 = np.mean(ve_vo2[i-window:i])
        after_vo2 = np.mean(ve_vo2[i:i+window])
        
        before_vco2 = np.mean(ve_vco2[i-window:i])
        after_vco2 = np.mean(ve_vco2[i:i+window])
        
        # Оба эквивалента растут
        vo2_increase = after_vo2 > before_vo2 * 1.05
        vco2_increase = after_vco2 > before_vco2 * 1.05
        
        if vo2_increase and vco2_increase:
            return power[i]
    
    return None
```

---

## Новые методы на основе HRV

### DFA Alpha-1

**Описание:** Detrended Fluctuation Analysis показывает переход от аэробного к анаэробному метаболизму.

**Пороговые значения:**
- DFA α1 ≈ 0.75 → VT1
- DFA α1 ≈ 0.50 → VT2

**Преимущества:**
- Неинвазивный метод только по ЧСС
- Может использоваться в полевых условиях
- Устройства: Kubios, Garmin (с поддержкой), COROS

**Ограничения:**
- Требует качественную запись R-R интервалов
- Чувствителен к артефактам

---

## Реализация в VO2max Report

### Модель порогов

```python
class Thresholds(models.Model):
    measurement = models.OneToOneField(Measurement, on_delete=models.CASCADE)
    
    # LT1 / VT1
    lt1_power = models.IntegerField(null=True)
    lt1_hr = models.IntegerField(null=True)
    lt1_vo2 = models.FloatField(null=True)
    lt1_lactate = models.FloatField(null=True)
    lt1_method = models.CharField(max_length=50)  # 'baseline_plus', 'loglog', 'v_slope', etc.
    
    # LT2 / VT2
    lt2_power = models.IntegerField(null=True)
    lt2_hr = models.IntegerField(null=True)
    lt2_vo2 = models.FloatField(null=True)
    lt2_lactate = models.FloatField(null=True)
    lt2_method = models.CharField(max_length=50)
    
    # VO2max
    vo2max_absolute = models.FloatField(null=True)  # мл/мин
    vo2max_relative = models.FloatField(null=True)  # мл/кг/мин
    power_at_vo2max = models.IntegerField(null=True)
    hr_at_vo2max = models.IntegerField(null=True)
    
    # Метаданные
    calculated_at = models.DateTimeField(auto_now=True)
    manually_adjusted = models.BooleanField(default=False)
```

### Сервис расчёта порогов

```python
class ThresholdCalculator:
    def __init__(self, measurement):
        self.measurement = measurement
        self.items = measurement.measurementitems.filter(use_in_report=True).order_by('time_seconds')
    
    def calculate_all(self):
        """Рассчитывает все пороги."""
        thresholds = Thresholds(measurement=self.measurement)
        
        # Данные
        power = [i.power for i in self.items]
        lactate = [i.lactate for i in self.items if i.lactate]
        vo2 = [i.vo2_ml_min for i in self.items]
        vco2 = [i.vco2_ml_min for i in self.items if i.vco2_ml_min]
        ve = [i.ve for i in self.items]
        hr = [i.hr for i in self.items]
        
        # LT1
        if lactate:
            thresholds.lt1_power = find_lt1_baseline_plus(power, lactate)
            thresholds.lt1_method = 'baseline_plus'
        else:
            thresholds.lt1_power = find_vt1_vslope(vo2, vco2, power)
            thresholds.lt1_method = 'v_slope'
        
        # LT2
        if lactate:
            thresholds.lt2_power = find_lt2_dmax(power, lactate)
            thresholds.lt2_method = 'dmax'
        else:
            thresholds.lt2_power = find_vt2_rcp(ve, vo2, vco2, power)
            thresholds.lt2_method = 'rcp'
        
        # VO2max
        thresholds.vo2max_absolute = max(vo2)
        thresholds.vo2max_relative = thresholds.vo2max_absolute / self.measurement.client.weight * 1000
        
        return thresholds
```

---

## Вопросы для дальнейшего исследования

1. **Валидация алгоритмов**
   - Какова точность автоматических методов vs экспертная оценка?
   - Какие методы лучше для разных типов спортсменов?

2. **Комбинирование методов**
   - Консенсус из нескольких методов?
   - Weighted average?

3. **Machine Learning подходы**
   - Есть ли модели ML для определения порогов?
   - Обучение на экспертных разметках

---

## Источники

1. Faude, O., et al. (2009). Lactate threshold concepts.
2. Binder, R. K., et al. (2008). Methodological approach to the determination of VT1 and VT2.
3. Santos-Concejero, J., et al. (2014). Validity of different methods for determining LT2.
4. Rogers, B., et al. (2021). DFA α1 as a novel, noninvasive threshold marker.

---

*Документ создан: 2025-12-28*
*Статус: Алгоритмы описаны, требуется валидация на реальных данных*
