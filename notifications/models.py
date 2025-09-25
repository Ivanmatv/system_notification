import re

from django.db import models


class ChannelConfig:
    """Конфигурация каналов отправки"""
    def __init__(self, emails=None, phones=None, telegram_chat_ids=None):
        self.emails = emails or []
        self.phones = [self._validate_phone(phone) for phone in (phones or [])]
        self.telegram_chat_ids = telegram_chat_ids or []
    
    def _validate_phone(self, phone):
        """Валидация номера телефона"""
        cleaned_phone = re.sub(r'[^\d+]', '', phone)
        if not cleaned_phone.startswith('+') and len(cleaned_phone) == 11:
            if cleaned_phone.startswith('8'):
                return '+7' + cleaned_phone[1:]
            elif cleaned_phone.startswith('7'):
                return '+' + cleaned_phone
        return cleaned_phone


class NotificationLog(models.Model):
    """Модель для логирования отправки"""

    class Status:
        SENT = 'sent'
        FAILED = 'failed'
        CHOICES = [(SENT, 'Отправлено'), (FAILED, 'Ошибка')]

    class Channel:
        EMAIL = 'email'
        SMS = 'sms'
        TELEGRAM = 'telegram'
        CHOICES = [(EMAIL, 'Email'), (SMS, 'SMS'), (TELEGRAM, 'Telegram')]

    # Контактные данныеы
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    telegram_chat_id = models.CharField(max_length=100, blank=True, null=True)

    # Сообщение
    title = models.CharField(max_length=200)
    message = models.TextField()

    # Статус отправки
    channel_used = models.CharField(max_length=10, choices=Channel.CHOICES)
    status = models.CharField(max_length=10, choices=Status.CHOICES)
    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @classmethod
    def create_log(cls, channel_used, status, title, message, 
                   email=None, phone=None, telegram_chat_id=None, error_message=None):
        """Создать запись в логе"""
        return cls.objects.create(
            email=email,
            phone=phone,
            telegram_chat_id=telegram_chat_id,
            title=title,
            message=message,
            channel_used=channel_used,
            status=status,
            error_message=error_message
        )