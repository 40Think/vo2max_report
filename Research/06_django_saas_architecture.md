# Deep Research: Django SaaS архитектура для спортивной аналитики

## Контекст проекта

**VO2max Report** — универсальная система анализа функциональной диагностики спортсменов. Приложение должно работать как локально (для отдельных лабораторий), так и в режиме SaaS для множества клиентов с разделением данных.

### Требования к архитектуре

- Multi-tenancy: изоляция данных между организациями
- Масштабируемость: поддержка растущего числа пользователей
- API: REST/GraphQL для интеграций
- Аутентификация: OAuth2, SSO

### Что нужно исследовать

1. **Multi-tenant архитектура в Django**
   - Shared database, row-level isolation
   - Shared database, separate schemas
   - Separate databases

2. **Выбор ORM подхода**
   - django-tenants
   - django-multitenant

3. **Scalability patterns**
   - Background tasks с Celery
   - Caching strategies
   - Database optimization

4. **API design**
   - Django REST Framework
   - Permissions и throttling

---

## Multi-Tenant архитектура

### Что такое Multi-Tenancy?

Multi-tenancy — архитектурный паттерн, где одно приложение обслуживает множество клиентов (tenants), сохраняя изоляцию их данных.

**Примеры tenants для VO2max Report:**
- Спортивные лаборатории
- Фитнес-клубы
- Университетские исследовательские центры
- Индивидуальные тренеры

---

### Стратегия 1: Shared Database, Row-Level Isolation

**Описание:** Все tenants хранятся в одной базе, данные разделяются по `tenant_id` в каждой таблице.

**Реализация:**
```python
# models.py
class Tenant(models.Model):
    name = models.CharField(max_length=100)
    domain = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

class TenantAwareModel(models.Model):
    """Базовая модель с привязкой к tenant."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    
    class Meta:
        abstract = True

class Client(TenantAwareModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    # ... остальные поля

class Measurement(TenantAwareModel):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    date = models.DateTimeField()
    # ...
```

**Middleware для определения tenant:**
```python
# middleware.py
from threading import local

_thread_locals = local()

def get_current_tenant():
    return getattr(_thread_locals, 'tenant', None)

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Определяем tenant по домену или header
        host = request.get_host().split(':')[0]
        
        try:
            tenant = Tenant.objects.get(domain=host)
        except Tenant.DoesNotExist:
            tenant = None
        
        _thread_locals.tenant = tenant
        request.tenant = tenant
        
        return self.get_response(request)
```

**Manager с автофильтрацией:**
```python
class TenantAwareManager(models.Manager):
    def get_queryset(self):
        tenant = get_current_tenant()
        if tenant:
            return super().get_queryset().filter(tenant=tenant)
        return super().get_queryset()

class Client(TenantAwareModel):
    objects = TenantAwareManager()
    all_tenants = models.Manager()  # Для админки
```

**Плюсы:**
- Простота реализации
- Одна база — проще бэкапы и миграции

**Минусы:**
- Риск data leakage при ошибках в фильтрации
- Сложнее масштабировать
- Все данные в одной схеме

---

### Стратегия 2: Shared Database, Separate Schemas (PostgreSQL)

**Описание:** Каждый tenant имеет свою PostgreSQL схему в одной базе данных.

**Библиотека:** django-tenants

**Установка:**
```bash
pip install django-tenants
```

**Конфигурация:**
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': 'vo2max',
        'USER': 'vo2max',
        'PASSWORD': 'secret',
        'HOST': 'localhost',
    }
}

DATABASE_ROUTERS = ('django_tenants.routers.TenantSyncRouter',)

MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',
    # ... остальные middleware
]

# Приложения в public схеме (общие для всех)
SHARED_APPS = [
    'django_tenants',
    'tenants',  # Наше приложение с моделью Tenant
    'django.contrib.auth',
    'django.contrib.contenttypes',
]

# Приложения в схеме каждого tenant
TENANT_APPS = [
    'core',  # Client, Measurement, MeasurementItem
    'reports',
]

INSTALLED_APPS = SHARED_APPS + TENANT_APPS

TENANT_MODEL = 'tenants.Tenant'
TENANT_DOMAIN_MODEL = 'tenants.Domain'
```

**Модели:**
```python
# tenants/models.py
from django_tenants.models import TenantMixin, DomainMixin

class Tenant(TenantMixin):
    name = models.CharField(max_length=100)
    paid_until = models.DateField(null=True)
    on_trial = models.BooleanField(default=True)
    created_on = models.DateField(auto_now_add=True)
    
    auto_create_schema = True

class Domain(DomainMixin):
    pass

# core/models.py — НЕ нужен tenant ForeignKey!
class Client(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    # Данные автоматически изолированы по схеме
```

**Создание tenant:**
```python
# Программно
tenant = Tenant(
    schema_name='lab_moscow',
    name='Московская спортивная лаборатория'
)
tenant.save()

domain = Domain(
    domain='moscow.vo2max.ru',
    tenant=tenant,
    is_primary=True
)
domain.save()
```

**Плюсы:**
- Строгая изоляция данных на уровне PostgreSQL
- Не нужно добавлять tenant_id в каждую модель
- Легко восстановить данные одного tenant

**Минусы:**
- Только PostgreSQL
- Миграции применяются ко всем схемам
- Больше схем → медленнее миграции

---

### Стратегия 3: Separate Databases Per Tenant

**Описание:** Каждый tenant имеет собственную базу данных.

**Когда использовать:**
- Максимальная изоляция
- Крупные enterprise клиенты
- Regulatory requirements (HIPAA, GDPR)

**Реализация:** Custom database router

```python
# routers.py
class TenantDatabaseRouter:
    def db_for_read(self, model, **hints):
        tenant = get_current_tenant()
        if tenant:
            return f'tenant_{tenant.id}'
        return 'default'
    
    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)
```

**Минусы:**
- Сложное управление
- Много баз данных = много ресурсов
- Сложнее cross-tenant аналитика

---

### Рекомендация для VO2max Report

**Выбор:** Стратегия 2 (django-tenants, separate schemas)

**Причины:**
- Хорошая изоляция данных (важно для медицинских данных)
- Не требует изменения всех моделей
- PostgreSQL — отличный выбор для аналитики
- Баланс между простотой и безопасностью

---

## Scalability Patterns

### 1. Background Tasks с Celery

**Зачем нужно:**
- Генерация отчётов (может занять 10-30 сек)
- Импорт больших CSV файлов
- Синхронизация с внешними платформами
- Отправка email уведомлений

**Установка:**
```bash
pip install celery redis
```

**Конфигурация:**
```python
# celery.py
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vo2max.settings')

app = Celery('vo2max')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

**Task для генерации отчёта:**
```python
# reports/tasks.py
from celery import shared_task
from .generators import DocxReportGenerator

@shared_task
def generate_report_async(measurement_id, format='docx'):
    """Асинхронная генерация отчёта."""
    from core.models import Measurement
    
    measurement = Measurement.objects.get(id=measurement_id)
    generator = DocxReportGenerator()
    
    report_bytes = generator.generate(measurement, format=format)
    
    # Сохранение в S3 или файловую систему
    filename = f'reports/{measurement_id}/report.{format}'
    # ...
    
    return filename
```

**Использование:**
```python
# views.py
def request_report(request, measurement_id):
    task = generate_report_async.delay(measurement_id, format='pdf')
    return JsonResponse({'task_id': task.id})

def check_report_status(request, task_id):
    result = AsyncResult(task_id)
    return JsonResponse({
        'status': result.status,
        'result': result.result if result.ready() else None
    })
```

---

### 2. Caching Strategies

**Уровни кэширования:**

1. **Query Cache** — кэширование результатов queryset
2. **View Cache** — кэширование ответов views
3. **Template Fragment Cache** — кэширование частей шаблонов
4. **Session Cache** — хранение сессий в Redis

**Конфигурация Redis cache:**
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

**Кэширование вычисляемых порогов:**
```python
from django.core.cache import cache

def get_thresholds(measurement_id):
    cache_key = f'thresholds_{measurement_id}'
    thresholds = cache.get(cache_key)
    
    if thresholds is None:
        thresholds = calculate_thresholds(measurement_id)
        cache.set(cache_key, thresholds, timeout=3600)  # 1 час
    
    return thresholds
```

---

### 3. Database Optimization

**Индексы:**
```python
class MeasurementItem(models.Model):
    measurement = models.ForeignKey(Measurement, on_delete=models.CASCADE)
    time_seconds = models.IntegerField()
    # ...
    
    class Meta:
        indexes = [
            models.Index(fields=['measurement', 'time_seconds']),
            models.Index(fields=['use_in_report']),
        ]
```

**select_related и prefetch_related:**
```python
# Плохо
measurements = Measurement.objects.all()
for m in measurements:
    print(m.client.name)  # N+1 queries!

# Хорошо
measurements = Measurement.objects.select_related('client').all()
for m in measurements:
    print(m.client.name)  # 1 query

# prefetch_related для многие-ко-многим
measurements = Measurement.objects.prefetch_related('measurementitems').all()
```

---

## API Design с Django REST Framework

### Установка
```bash
pip install djangorestframework
```

### Конфигурация
```python
# settings.py
INSTALLED_APPS = [
    # ...
    'rest_framework',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

### Serializers
```python
# serializers.py
from rest_framework import serializers

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'first_name', 'last_name', 'birth_date', 'height', 'weight']

class MeasurementItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementItem
        fields = ['id', 'time_seconds', 'vo2_ml_min', 'hr', 'power', 'lactate']

class MeasurementSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    items = MeasurementItemSerializer(many=True, read_only=True, source='measurementitems')
    
    class Meta:
        model = Measurement
        fields = ['id', 'client', 'date', 'start_power', 'power_step', 'items']
```

### ViewSets
```python
# views.py
from rest_framework import viewsets, permissions

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Автоматическая фильтрация по tenant (для django-tenants)
        return super().get_queryset()

class MeasurementViewSet(viewsets.ModelViewSet):
    queryset = Measurement.objects.select_related('client').prefetch_related('measurementitems')
    serializer_class = MeasurementSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтрация по клиенту
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        return queryset
```

### URLs
```python
# urls.py
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'clients', ClientViewSet)
router.register(r'measurements', MeasurementViewSet)

urlpatterns = [
    path('api/v1/', include(router.urls)),
]
```

---

## Docker и развёртывание

### docker-compose.yml для development
```yaml
version: '3.8'

services:
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DEBUG=1
      - DATABASE_URL=postgres://vo2max:vo2max@db:5432/vo2max
      - REDIS_URL=redis://redis:6379/0

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=vo2max
      - POSTGRES_USER=vo2max
      - POSTGRES_PASSWORD=vo2max

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  celery:
    build: .
    command: celery -A vo2max worker -l info
    volumes:
      - .:/app
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgres://vo2max:vo2max@db:5432/vo2max
      - REDIS_URL=redis://redis:6379/0

volumes:
  postgres_data:
  redis_data:
```

---

## Вопросы для дальнейшего исследования

1. **Billing и subscription management**
   - Интеграция с Stripe/Paddle
   - Ограничение features по плану

2. **Multi-region deployment**
   - Хранение данных в регионе клиента (GDPR)
   - CDN для статических файлов

3. **Monitoring и observability**
   - Sentry для ошибок
   - Prometheus + Grafana для метрик

4. **CI/CD pipeline**
   - GitHub Actions / GitLab CI
   - Automated testing
   - Blue-green deployment

---

## Источники

1. django-tenants: https://django-tenants.readthedocs.io/
2. Django REST Framework: https://www.django-rest-framework.org/
3. Celery: https://docs.celeryq.dev/
4. Django Documentation: https://docs.djangoproject.com/

---

*Документ создан: 2025-12-28*
*Статус: Архитектура определена, готово к имплементации*
