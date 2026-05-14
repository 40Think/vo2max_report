# Deep Research: Безопасность медицинских данных (GDPR, HIPAA)

## Контекст проекта

VO2max Report обрабатывает чувствительные медицинские данные спортсменов (HR, физиологические параметры, биометрия). Требуется соответствие международным стандартам защиты данных.

---

## GDPR (General Data Protection Regulation)

### Применимость

GDPR применяется если:
- Пользователи находятся в ЕС
- Организация обрабатывает данные граждан ЕС
- Данные хранятся на серверах в ЕС

### Ключевые требования

1. **Lawful Basis** — законное основание для обработки
   - Согласие пользователя
   - Выполнение договора
   - Законные интересы

2. **Explicit Consent** — явное согласие
   - Checkbox при регистрации
   - Чёткое описание целей обработки
   - Возможность отзыва

3. **Data Minimization** — минимизация данных
   - Собирать только необходимое
   - Удалять неиспользуемые данные

4. **Right to Access** — право на доступ
   - Пользователь может запросить свои данные
   - Срок ответа: 30 дней

5. **Right to Erasure** — право на удаление ("забвение")
   - Полное удаление данных по запросу
   - Удаление из backup'ов

6. **Data Portability** — переносимость данных
   - Экспорт данных в машиночитаемом формате
   - JSON, CSV, XML

7. **Breach Notification** — уведомление об утечках
   - 72 часа на уведомление регулятора
   - Уведомление пострадавших пользователей

---

## HIPAA (Health Insurance Portability and Accountability Act)

### Применимость

HIPAA применяется в США если:
- Организация является "covered entity" (healthcare provider)
- Или "business associate" covered entity
- Обрабатывается PHI (Protected Health Information)

### Для спортивного приложения

Фитнес-приложения обычно НЕ подпадают под HIPAA, кроме случаев:
- Интеграция с healthcare providers
- Обработка данных health insurance
- Явная связь с медицинским лечением

### Ключевые требования (если применимо)

1. **Privacy Rule** — правила конфиденциальности
2. **Security Rule** — технические меры защиты
3. **Breach Notification** — уведомление об инцидентах

---

## Django Security Best Practices

### 1. Аутентификация и авторизация

```python
# settings.py
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Время жизни сессии
SESSION_COOKIE_AGE = 3600  # 1 час
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# HTTPS only
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
```

### 2. Шифрование данных

```python
# Шифрование чувствительных полей
from django_cryptography.fields import encrypt

class Client(models.Model):
    first_name = models.CharField(max_length=100)
    # Зашифрованные поля
    contact_info = encrypt(models.TextField(blank=True))
    medical_notes = encrypt(models.TextField(blank=True))
```

### 3. Audit Logging

```python
# Логирование доступа к данным
import logging

logger = logging.getLogger('audit')

class ClientViewSet(viewsets.ModelViewSet):
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        logger.info(f"User {request.user.id} accessed client {instance.id}")
        return super().retrieve(request, *args, **kwargs)

# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'audit_file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/vo2max/audit.log',
        },
    },
    'loggers': {
        'audit': {
            'handlers': ['audit_file'],
            'level': 'INFO',
        },
    },
}
```

### 4. GDPR Consent Management

```python
class ConsentRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    purpose = models.CharField(max_length=100)  # 'data_processing', 'marketing'
    granted = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()

class GDPRMixin:
    """Миксин для GDPR-compliant views."""
    
    def check_consent(self, user, purpose):
        consent = ConsentRecord.objects.filter(
            user=user, purpose=purpose, granted=True
        ).exists()
        if not consent:
            raise PermissionDenied("Consent not granted")
```

### 5. Data Export

```python
def export_user_data(user):
    """GDPR: экспорт данных пользователя."""
    data = {
        'profile': {
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        },
        'clients': [],
        'measurements': [],
    }
    
    for client in Client.objects.filter(user=user):
        client_data = {
            'name': client.full_name,
            'measurements': []
        }
        for m in client.measurements.all():
            client_data['measurements'].append({
                'date': m.date.isoformat(),
                'items': list(m.measurementitems.values())
            })
        data['clients'].append(client_data)
    
    return data
```

### 6. Data Deletion

```python
def delete_user_data(user):
    """GDPR: полное удаление данных пользователя."""
    # Удаление связанных данных
    for client in Client.objects.filter(user=user):
        client.measurements.all().delete()
    Client.objects.filter(user=user).delete()
    
    # Анонимизация пользователя (вместо удаления)
    user.email = f'deleted_{user.id}@anonymized.local'
    user.first_name = 'Deleted'
    user.last_name = 'User'
    user.is_active = False
    user.save()
```

---

## Чеклист безопасности

### Обязательно (Mandatory)

- [ ] HTTPS для всех соединений
- [ ] Хеширование паролей (Django по умолчанию)
- [ ] CSRF protection (Django по умолчанию)
- [ ] SQL injection protection (ORM по умолчанию)
- [ ] Шифрование чувствительных данных
- [ ] Audit logging
- [ ] Consent management
- [ ] Data export endpoint
- [ ] Data deletion endpoint
- [ ] Session timeout
- [ ] Rate limiting

### Рекомендовано

- [ ] 2FA authentication
- [ ] IP whitelisting для API
- [ ] Regular security audits
- [ ] Penetration testing
- [ ] Backup encryption
- [ ] Data retention policies

---

## Источники

1. GDPR Official: https://gdpr.eu/
2. Django Security: https://docs.djangoproject.com/en/5.0/topics/security/
3. HIPAA Overview: https://www.hhs.gov/hipaa/
4. django-gdpr-assist: https://github.com/wildfish/django-gdpr-assist

---

*Документ создан: 2025-12-28*
*Статус: Основные требования определены*
