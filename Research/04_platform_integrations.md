# Deep Research: Интеграция с Garmin, Polar, Suunto и другими платформами

## Контекст проекта

**VO2max Report** — универсальная система анализа функциональной диагностики спортсменов. Для расширения возможностей системы необходимо интегрироваться с популярными платформами спортивных носимых устройств для получения данных HR, мощности, GPS и других метрик.

### Почему это важно

- Спортсмены уже используют Garmin/Polar/Suunto для ежедневных тренировок
- Интеграция позволит загружать данные автоматически
- Можно отслеживать progress между лабораторными тестами
- Валидация лабораторных порогов на полевых данных

### Что нужно исследовать

1. **Официальные API производителей**
   - Garmin Health API / Connect API
   - Polar Flow API
   - Suunto App API
   - Wahoo Cloud API

2. **Python библиотеки-обёртки**
   - python-garminconnect
   - polar-accesslink
   - Неофициальные решения

3. **Условия доступа и ограничения**
   - Требования для разработчиков
   - Rate limits
   - Стоимость

4. **Альтернативные платформы-агрегаторы**
   - Strava API
   - Training Peaks API
   - Intervals.icu

---

## Garmin Connect

### Официальный Garmin Developer Program

**URL:** https://developer.garmin.com/

**Типы API:**

| API | Описание | Доступ |
|-----|----------|--------|
| **Health API** | Доступ к health metrics (HR, sleep, stress, activity) | Business only |
| **Activity API** | Скачивание FIT файлов активностей | Business only |
| **Connect API** | Web services для приложений | Device development |

**Условия доступа:**
- API доступен только для **бизнес-разработчиков**
- Требуется заявка и одобрение Garmin
- Персональное использование **не поддерживается**
- Бесплатно после одобрения

**Авторизация:** OAuth 1.0a

**Формат данных:** JSON, FIT files

---

### Python библиотеки для Garmin

#### 1. python-garminconnect

**GitHub:** https://github.com/cyberjunky/python-garminconnect

**Описание:** Неофициальная Python обёртка для Garmin Connect

**Установка:**
```bash
pip install garminconnect
```

**Пример использования:**
```python
from garminconnect import Garmin

# Авторизация
client = Garmin("email@example.com", "password")
client.login()

# Получение данных HR за день
hr_data = client.get_heart_rates(date.today())
print(hr_data)

# Получение активностей
activities = client.get_activities(0, 10)  # последние 10 активностей

# Скачивание FIT файла
for activity in activities:
    activity_id = activity['activityId']
    fit_data = client.download_activity(activity_id, dl_fmt=client.ActivityDownloadFormat.ORIGINAL)
    
    with open(f'{activity_id}.fit', 'wb') as f:
        f.write(fit_data)
```

**Доступные методы:**
- `get_heart_rates(date)` — HR за день
- `get_activities(start, limit)` — список активностей
- `download_activity(id, format)` — скачать FIT/TCX/GPX
- `get_body_composition(date)` — вес и композиция тела
- `get_sleep_data(date)` — данные сна
- `get_stress_data(date)` — уровень стресса

**Ограничения:**
- Неофициальный API — может сломаться при изменениях Garmin
- Использует web-scraping и внутренние endpoints
- Rate limits не документированы

---

#### 2. Garth

**GitHub:** https://github.com/matin/garth

**Описание:** Современная OAuth-based библиотека для Garmin Connect

**Преимущества:**
- Использует OAuth (более стабильно)
- Хранит токены для повторного использования

```python
import garth

# Авторизация
garth.login("email@example.com", "password")
garth.save("~/.garth")

# Позже загрузить сессию
garth.resume("~/.garth")

# API запросы
activities = garth.connectapi("/activitylist-service/activities/search/activities")
```

---

## Polar

### Polar AccessLink API

**URL:** https://www.polar.com/accesslink-api

**Описание:** Официальный API для доступа к данным Polar Flow

**Регистрация:**
1. Создать аккаунт разработчика на Polar AccessLink
2. Зарегистрировать приложение
3. Получить Client ID и Client Secret

**Авторизация:** OAuth 2.0

**Доступные данные:**
- Daily activity (шаги, калории, active time)
- Training sessions (HR, GPS, zones)
- Physical information (вес, рост)
- Sleep data

**Python библиотека:** polar-accesslink

```bash
pip install accesslink
```

**Пример:**
```python
from accesslink import AccessLink

accesslink = AccessLink(client_id='YOUR_CLIENT_ID', client_secret='YOUR_CLIENT_SECRET')

# OAuth authorization flow
auth_url = accesslink.authorization_url

# After user authorization, exchange code for token
token = accesslink.get_access_token(authorization_code)

# Get user info
user_info = accesslink.users.get_information(access_token=token['access_token'])

# Get training sessions
trainings = accesslink.training_data.list_exercises(access_token=token['access_token'])
```

**Ограничения:**
- Rate limits: 100 requests per minute
- Данные доступны после синхронизации устройства

---

## Suunto

### Suunto App API

**Статус:** Ограниченный доступ

**Описание:** Suunto предоставляет API через партнёрскую программу

**Альтернативный подход:**
- Экспорт через Suunto App → FIT/GPX файлы
- Синхронизация с Strava и использование Strava API

---

## Wahoo

### Wahoo Cloud API

**Статус:** Ограниченный доступ для партнёров

**Доступные данные:**
- Workouts
- User profile
- Device data (Wahoo KICKR, ELEMNT)

**Альтернатива:**
- Wahoo синхронизируется с Strava
- Использовать Strava API

---

## Strava API

### Описание

**URL:** https://developers.strava.com/

Strava — популярная платформа-агрегатор, куда синхронизируются данные со многих устройств.

### Регистрация приложения

1. Зайти на https://www.strava.com/settings/api
2. Создать приложение
3. Получить Client ID и Client Secret

### Авторизация

OAuth 2.0 с scopes:
- `read` — публичные данные
- `activity:read` — чтение активностей
- `activity:read_all` — все активности включая приватные

### Python библиотека: stravalib

```bash
pip install stravalib
```

**Пример:**
```python
from stravalib.client import Client

client = Client()

# Authorization URL
authorize_url = client.authorization_url(
    client_id=YOUR_CLIENT_ID,
    redirect_uri='http://localhost:8000/callback',
    scope=['read', 'activity:read_all']
)

# Exchange code for token
token_response = client.exchange_code_for_token(
    client_id=YOUR_CLIENT_ID,
    client_secret=YOUR_CLIENT_SECRET,
    code=CODE_FROM_CALLBACK
)

client.access_token = token_response['access_token']

# Get athlete info
athlete = client.get_athlete()
print(athlete.firstname, athlete.lastname)

# Get activities
activities = client.get_activities(limit=10)
for activity in activities:
    print(activity.name, activity.distance, activity.average_heartrate)

# Get activity streams (detailed data)
streams = client.get_activity_streams(
    activity_id=12345,
    types=['time', 'heartrate', 'watts', 'cadence', 'altitude']
)
```

### Rate Limits

- 100 requests / 15 minutes
- 1000 requests / day

### Доступные данные

| Endpoint | Описание |
|----------|----------|
| `/athlete` | Профиль атлета |
| `/activities` | Список активностей |
| `/activities/{id}` | Детали активности |
| `/activities/{id}/streams` | Поточные данные (HR, power, GPS) |
| `/segments` | Сегменты маршрутов |

---

## Training Peaks

### TrainingPeaks Developer API

**URL:** https://developers.trainingpeaks.com/

**Доступ:** Требуется партнёрство

**Доступные данные:**
- Workouts
- Workout files (FIT, TCX)
- Metrics (TSS, IF, NP)
- Athlete profile

**Формат:** REST API, JSON

---

## Intervals.icu

### Intervals.icu API

**URL:** https://intervals.icu/api

**Описание:** Бесплатная платформа для анализа тренировок с открытым API

**Авторизация:** API Key (в настройках профиля)

**Python пример:**
```python
import requests

API_KEY = 'your_api_key'
ATHLETE_ID = 'i12345'

headers = {
    'Authorization': f'Basic {API_KEY}'
}

# Get activities
response = requests.get(
    f'https://intervals.icu/api/v1/athlete/{ATHLETE_ID}/activities',
    headers=headers
)
activities = response.json()

# Get activity details with streams
activity_id = 'i12345678'
response = requests.get(
    f'https://intervals.icu/api/v1/activity/{activity_id}',
    headers=headers
)
```

**Доступные данные:**
- Activities
- Streams (HR, power, cadence, etc.)
- Wellness data
- Fitness/Fatigue metrics

**Преимущества:**
- Бесплатный API
- Поддержка импорта со многих устройств
- Продвинутая аналитика

---

## Архитектура интеграций в VO2max Report

### Модель для хранения подключений

```python
class PlatformConnection(models.Model):
    """Подключение к внешней платформе."""
    
    PLATFORM_CHOICES = [
        ('garmin', 'Garmin Connect'),
        ('polar', 'Polar Flow'),
        ('suunto', 'Suunto App'),
        ('strava', 'Strava'),
        ('intervals', 'Intervals.icu'),
        ('trainingpeaks', 'Training Peaks'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    
    # OAuth tokens
    access_token = models.TextField()
    refresh_token = models.TextField(null=True)
    token_expires_at = models.DateTimeField(null=True)
    
    # Platform-specific user ID
    external_user_id = models.CharField(max_length=100, null=True)
    
    # Settings
    auto_sync = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'platform']
```

### Сервис синхронизации

```python
from abc import ABC, abstractmethod

class BasePlatformSync(ABC):
    """Базовый класс для синхронизации с платформами."""
    
    @abstractmethod
    def authenticate(self, connection: PlatformConnection) -> bool:
        """Проверить и обновить токены."""
        pass
    
    @abstractmethod
    def get_activities(self, start_date: date, end_date: date) -> list:
        """Получить список активностей."""
        pass
    
    @abstractmethod
    def download_activity(self, activity_id: str) -> bytes:
        """Скачать FIT/TCX файл активности."""
        pass


class StravaSync(BasePlatformSync):
    """Синхронизация со Strava."""
    
    def __init__(self, connection: PlatformConnection):
        self.connection = connection
        self.client = Client()
        self.client.access_token = connection.access_token
    
    def authenticate(self) -> bool:
        if self.connection.token_expires_at < timezone.now():
            # Refresh token
            new_token = self.client.refresh_access_token(
                client_id=settings.STRAVA_CLIENT_ID,
                client_secret=settings.STRAVA_CLIENT_SECRET,
                refresh_token=self.connection.refresh_token
            )
            self.connection.access_token = new_token['access_token']
            self.connection.refresh_token = new_token['refresh_token']
            self.connection.token_expires_at = datetime.fromtimestamp(new_token['expires_at'])
            self.connection.save()
        return True
    
    def get_activities(self, start_date, end_date):
        return list(self.client.get_activities(
            after=start_date,
            before=end_date
        ))
    
    def download_activity(self, activity_id):
        streams = self.client.get_activity_streams(
            activity_id=activity_id,
            types=['time', 'heartrate', 'watts', 'cadence', 'distance', 'altitude']
        )
        return streams
```

---

## Рекомендации для реализации

### Phase 1: Базовая интеграция

1. **Strava API** — самый доступный и популярный
2. **Intervals.icu** — бесплатный, хорошая аналитика
3. **Ручной импорт FIT/TCX** — универсальный fallback

### Phase 2: Премиум интеграции

1. **Garmin Connect** через python-garminconnect (неофициально)
2. **Polar AccessLink** (официальный API)

### Phase 3: Enterprise

1. **Garmin Health API** (требует бизнес-партнёрство)
2. **TrainingPeaks API** (партнёрство)

---

## Вопросы для дальнейшего исследования

1. **Webhook vs Polling**
   - Какие платформы поддерживают webhooks?
   - Как настроить real-time синхронизацию?

2. **Data Mapping**
   - Как нормализовать данные из разных источников?
   - Разрешение конфликтов (одна активность из нескольких источников)

3. **Privacy и Consent**
   - GDPR требования для хранения данных из внешних платформ
   - Политика удаления данных

---

## Источники

1. Garmin Developer Program: https://developer.garmin.com/
2. Polar AccessLink: https://www.polar.com/accesslink-api
3. Strava API: https://developers.strava.com/
4. Intervals.icu API: https://intervals.icu/api
5. python-garminconnect: https://github.com/cyberjunky/python-garminconnect
6. stravalib: https://github.com/stravalib/stravalib

---

*Документ создан: 2025-12-28*
*Статус: Основная информация собрана, требуется тестирование API*
