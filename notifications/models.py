from django.db import models
from django.contrib.auth.models import User


class NotificationPreference(models.Model):
    NOTIFICATION_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('telegram', 'Telegram'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    telegram_chat_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ['user', 'notification_type']
        ordering = ['priority']


class Notification(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает отправки'),
        ('sent', 'Отправлено'),
        ('failed', 'Не удалось отправить'),
        ('retrying', 'Повторная попытка'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=NotificationPreference.NOTIFICATION_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)

    class Meta:
        ordering = ['-created_at']


class NotificationLog(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    attempt_number = models.IntegerField()
    channel_used = models.CharField(max_length=10, choices=NotificationPreference.NOTIFICATION_TYPES)
    status = models.CharField(max_length=10, choices=Notification.STATUS_CHOICES)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)