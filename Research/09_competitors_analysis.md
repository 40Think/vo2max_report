# Deep Research: Конкуренты и существующие решения

## Контекст проекта

VO2max Report — универсальная система анализа функциональной диагностики. Необходимо изучить существующие решения для понимания рынка и выявления конкурентных преимуществ.

---

## Крупные платформы

### TrainingPeaks

**URL:** https://www.trainingpeaks.com/

**Описание:** Лидер рынка для тренеров и спортсменов на выносливость.

**Ключевые функции:**
- Планирование тренировок с TSS/IF/NP
- Анализ активностей
- WKO5 integration для глубокой аналитики
- Calendar-based planning
- Coach-athlete communication

**Цена:** $9.95-$19.95/мес (athlete), $49+/мес (coach)

**Преимущества:**
- Стандарт индустрии
- Огромная база пользователей
- Интеграция со всеми устройствами

**Недостатки:**
- Нет поддержки лабораторных тестов
- Фокус на тренировках, не на диагностике
- Дорого для coaches

---

### WKO5

**URL:** https://www.trainingpeaks.com/wko5/

**Описание:** Продвинутый desktop software для аналитики.

**Ключевые функции:**
- Power Duration Curve (PDC)
- Phenotype analysis
- Individual Power-HR relationship
- FTP estimation
- Custom charts и analytics

**Цена:** $179 единоразово + $89/год обновления

**Преимущества:**
- Глубочайшая аналитика в индустрии
- Индивидуальные модели

**Недостатки:**
- Desktop only (Windows/Mac)
- Крутая кривая обучения
- Нет web/mobile

---

### Intervals.icu

**URL:** https://intervals.icu/

**Описание:** Бесплатная платформа для анализа тренировок. Популярная альтернатива TrainingPeaks.

**Ключевые функции:**
- Fitness/Fatigue/Form graphs
- Power analysis (CP, W')
- HR zones
- Training load
- Calendar и planning
- API для интеграций

**Цена:** Бесплатно (донаты приветствуются)

**Преимущества:**
- Бесплатно
- Отличная аналитика
- Хорошее API
- Активное развитие

**Недостатки:**
- Один разработчик
- Нет лабораторных тестов
- Ограниченная поддержка

---

### Strava

**URL:** https://www.strava.com/

**Описание:** Социальная сеть для спортсменов.

**Ключевые функции:**
- GPS tracking
- Segments и leaderboards
- Social features
- Basic training log
- Fitness/Freshness (premium)

**Цена:** Бесплатно / $11.99/мес (premium)

**Преимущества:**
- Огромное сообщество
- Простота использования
- Социальные функции

**Недостатки:**
- Минимальная аналитика
- Нет диагностики
- Фокус на outdoor активностях

---

### Golden Cheetah

**URL:** https://www.goldencheetah.org/

**Описание:** Open-source desktop software для анализа.

**Ключевые функции:**
- Анализ power/HR данных
- Custom charts
- Workouts library
- CP/W' models
- Local storage

**Цена:** Бесплатно (open-source)

**Преимущества:**
- Бесплатно
- Очень гибкий
- Работает локально

**Недостатки:**
- Устаревший интерфейс
- Сложно для новичков
- Нет cloud sync

---

## Специализированные решения для диагностики

### COSMED OMNIA

**URL:** https://www.cosmed.com/

**Описание:** Программное обеспечение для устройств COSMED.

**Функции:**
- Анализ газообмена
- VO2max reports
- Threshold detection
- Integration с оборудованием COSMED

**Ограничения:**
- Только для оборудования COSMED
- Проприетарное
- Нет интеграций

---

### Cortex MetaSoft Studio

**URL:** https://www.cortex-medical.com/

**Описание:** Софт для газоанализаторов Cortex.

**Функции:**
- Real-time мониторинг
- Анализ данных
- Report generation

**Ограничения:**
- Только Cortex устройства
- Windows only

---

### VO2 Master

**URL:** https://vo2master.com/

**Описание:** Portable metabolic analyzer с облачной платформой.

**Функции:**
- Live VO2 tracking
- Cloud data storage
- Basic reports
- Integration со Strava/TrainingPeaks

**Преимущества:**
- Portable device
- Относительно доступный
- Хорошие интеграции

**Недостатки:**
- Ограниченная точность vs лабораторные
- Проприетарная экосистема

---

### PNOE

**URL:** https://www.pfreediv.com/

**Описание:** Metabolic analyzer с focus на fitness.

**Функции:**
- Metabolic testing
- Personalized reports
- Nutrition recommendations

**Ограничения:**
- Проприетарная система
- Фокус на клинике/gym

---

## Конкурентные преимущества VO2max Report

### Уникальное ценностное предложение

| Функция | TrainingPeaks | Intervals.icu | Golden Cheetah | VO2max Report |
|---------|---------------|---------------|----------------|---------------|
| Лабораторные тесты | ❌ | ❌ | ❌ | ✅ |
| Мультибренд парсеры | ⚠️ | ⚠️ | ✅ | ✅ |
| Порог detection | ❌ | ⚠️ | ✅ | ✅ |
| Лактат данные | ❌ | ❌ | ⚠️ | ✅ |
| DOCX reports | ❌ | ❌ | ⚠️ | ✅ |
| Open-source | ❌ | ❌ | ✅ | ✅ |
| Web + Local | ✅ | ✅ | ❌ | ✅ |
| Кастомизация | ❌ | ⚠️ | ✅ | ✅ |

### Ключевые дифференциаторы

1. **Универсальность парсеров**
   - Поддержка COSMED, Cortex, PNOE, любых CSV
   - Не привязан к производителю

2. **Лабораторная специализация**
   - Лактат измерения
   - Автоматическое определение порогов
   - Профессиональные отчёты

3. **Гибкость развёртывания**
   - Локально для одной лаборатории
   - SaaS для сети клиник
   - Docker для enterprise

4. **Open-source подход**
   - Прозрачность
   - Кастомизация
   - Community contributions

---

## Target Market

### Primary (Первичный рынок)

1. **Спортивные лаборатории**
   - Университетские
   - Частные диагностические центры
   - Спортивные клубы elite level

2. **Спортивные врачи и физиологи**
   - Нужны профессиональные отчёты
   - Работают с разным оборудованием

### Secondary (Вторичный рынок)

1. **Тренеры**
   - Используют данные лабораторий
   - Нужна интеграция с их системами

2. **Исследователи**
   - Академические институты
   - Научные публикации

---

## Pricing Strategy

### Модели ценообразования конкурентов

| Продукт | Модель | Цена |
|---------|--------|------|
| TrainingPeaks | Subscription | $9.95-$119/мес |
| WKO5 | One-time + annual | $179 + $89/год |
| Intervals.icu | Donation | Бесплатно |
| Golden Cheetah | Open-source | Бесплатно |

### Рекомендация для VO2max Report

1. **Free Tier**
   - Базовый функционал
   - Ограничение по количеству клиентов
   - Community support

2. **Professional ($29/мес)**
   - Unlimited клиенты
   - Все парсеры
   - Email support

3. **Enterprise (Custom)**
   - On-premise deployment
   - White-label branding
   - API access
   - SLA support

---

## Источники

1. TrainingPeaks: https://www.trainingpeaks.com/
2. Intervals.icu: https://intervals.icu/
3. Golden Cheetah: https://www.goldencheetah.org/
4. COSMED: https://www.cosmed.com/
5. VO2 Master: https://vo2master.com/

---

*Документ создан: 2025-12-28*
*Статус: Анализ конкурентов завершён*
