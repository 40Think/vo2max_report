# Deep Research Plan: Machine Learning для определения порогов

## Контекст

На основе исследования алгоритмов порогов (answers/3.md) выявлена перспективность ML-подходов для автоматического определения VT1/VT2 и LT1/LT2 с точностью, сравнимой с экспертной оценкой.

## Цели исследования

### 1. Обзор существующих ML-моделей

**Задачи:**
- Найти опубликованные модели для threshold detection
- Изучить архитектуры (CNN, RNN, Transformer)
- Сравнить accuracy vs традиционные методы

**Запросы:**
1. Machine learning ventilatory threshold detection VO2max research papers
2. Deep learning lactate threshold prediction cycling
3. Neural network exercise physiology threshold classification
4. Automated anaerobic threshold detection algorithms comparison
5. Time series classification exercise testing ML models

---

### 2. Подготовка датасета

**Задачи:**
- Найти публичные датасеты с экспертной разметкой
- Определить требования к собственному датасету
- Разработать протокол экспертной разметки

**Запросы:**
1. Public VO2max testing datasets with threshold annotations
2. Exercise physiology research datasets open access
3. Gold standard lactate threshold expert determination protocol
4. Inter-rater reliability ventilatory threshold determination
5. CPET cardiopulmonary exercise testing database

---

### 3. Архитектура модели

**Задачи:**
- Выбрать оптимальную архитектуру для временных рядов
- Разработать feature engineering pipeline
- Определить метрики качества

**Запросы:**
1. LSTM vs Transformer time series threshold detection
2. Feature engineering exercise physiology data
3. Multi-task learning physiological thresholds prediction
4. Uncertainty quantification ML medical predictions
5. Explainable AI exercise testing threshold detection

---

### 4. Валидация и интерпретируемость

**Задачи:**
- Cross-validation стратегия
- SHAP/LIME для объяснения предсказаний
- Сравнение с экспертами (Bland-Altman)

**Запросы:**
1. Bland-Altman analysis threshold detection validation
2. SHAP interpretability physiological predictions
3. Leave-one-subject-out cross validation exercise data
4. Clinical validation ML exercise testing
5. Explainable threshold detection sports science

---

### 5. Персонализация моделей

**Задачи:**
- Transfer learning для адаптации под спортсмена
- Fine-tuning на исторических данных
- Online learning при повторных тестах

**Запросы:**
1. Personalized machine learning athlete performance
2. Transfer learning exercise physiology individual adaptation
3. Online learning athlete monitoring threshold tracking
4. Few-shot learning physiological threshold detection
5. Domain adaptation sports science ML models

---

## Ожидаемые результаты

1. Обзор SOTA в ML threshold detection
2. Спецификация датасета и протокола разметки
3. Прототип ML-pipeline в PyTorch/TensorFlow
4. Benchmark против традиционных методов
5. Интеграция в VO2max Report с confidence scores

## Риски

- Недостаточный объём размеченных данных
- Переобучение на малых выборках
- Требования к вычислительным ресурсам

---

*План создан: 2025-12-28*
*Приоритет: Средний (R&D направление)*
