# Система уведомлений

Это Django-приложение для системы уведомлений, которое позволяет отправлять сообщения пользователям через различные каналы: email, SMS и Telegram. Поддерживается синхронная и асинхронная отправка (с использованием Celery), логирование уведомлений и статистика. API построено на Django REST Framework с автоматической документацией через Swagger.

## 🚀 Функциональность

### Отправка уведомлений:
- Одному пользователю.
- Массово (по спискам контактов).
- По списку пользователей с индивидуальными контактами.

- Приоритет каналов: Email → SMS → Telegram (с возможностью указать предпочтительный канал).
- Асинхронная отправка: Через Celery для обработки больших объемов.
- Логирование: Хранение истории отправок в модели NotificationLog.
- Документация API: Автоматически генерируется с примерами запросов.

## 📋 Требования
- Python 3.11
- Django 5.x
- Django REST Framework
- Celery (для асинхронной отправки)
- Redis (как брокер для Celery)
- Библиотеки для отправки: smtplib (email), SMSru (SMS), python-telegram-bot (Telegram)

## ⚙️ Установка
1. Клонируйте репозиторий:
```bash
  git clone https://github.com/Ivanmatv/system_notification.git
  cd system_notification
```
2. Создайте и активируйте виртуальное окружение:
```bash
  python -m venv venv
  source venv/bin/activate  # Для Windows: venv\Scripts\activate
```
3. Установите зависимости:
```bash
  pip install -r requirements.txt
```

4. Настройка сервисов отправки
### Email (Yandex)
- Включите двухфакторную аутентификацию
- Создайте пароль приложения
- Укажите данные в .env файле
### SMS (SMS.ru)
- Зарегистрируйтесь на SMS.ru
- Получите API ID в личном кабинете
- Укажите в настройках
### Telegram
- Создайте бота через @BotFather
- Получите токен бота
- Укажите в настройках

5. Настройте переменные окружения (в .env файле или напрямую)
### django settings.py
- `SECRET_KEY`
### База данных
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
### Настройки email
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USE_SSL`
- `EMAIL_USE_TLS`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
### Для SMS
- `SMSRU_API_ID`
### Telegram
- `TELEGRAM_BOT_TOKEN`
### Celery настройки
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

5. Примените миграции
```bash
  python manage.py makemigrations
  python manage.py migrate
```
5. Создайте суперюзера
```bash
  python manage.py createsuperuser
```

# Запуск
## Локально
1. Запустите сервер Django:
```bash
  python manage.py runserver
```
2. Запустите Celery worker для асинхронных задач:
```bash
  celery -A system_notification worker -l info
```
API будет доступно по адресу http://127.0.0.1:8000/
## С Docker
1. Соберите и запустите контейнеры:
```bash
  docker-compose up --build
```
Это запустит Django, Celery и Redis.

# 📡 API Документация
После запуска сервера документация доступна по адресам:

ReDoc: http://localhost:8000/redoc/

Swagger UI: http://localhost:8000/swagger/

# 📡 Использование
Отправка сообщения одному пользователю
```bash
curl -X POST http://localhost:8000/api/notifications/send/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Тестовое сообщение",
    "message": "Это тестовое сообщение",
    "email": "user@example.com",
    "phone": "+79161234567",
    "telegram_chat_id": "123456789",
    "preferred_channel": "email"
  }'
```
Массовая отправка
```bash
curl -X POST http://localhost:8000/api/notifications/send/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Массовое уведомление",
    "message": "Сообщение для всех пользователей",
    "emails": ["user1@example.com", "user2@example.com"],
    "phones": ["+79161234567", "+79161234568"],
    "telegram_chat_ids": ["123456789", "987654321"]
  }'
```
Асинхронная отправка
```bash
curl -X POST http://localhost:8000/api/notifications/send-async/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Асинхронное сообщение",
    "message": "Отправляется в фоне",
    "emails": ["user1@example.com", "user2@example.com"]
  }'
```
Просмотр логов
```bash
curl http://localhost:8000/api/notifications/logs/
```
# 🔧 Администрирование
### Доступ к админке
URL: http://localhost:8000/admin/

Логин: данные от суперпользователя
