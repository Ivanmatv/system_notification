from datetime import timezone
import logging
import requests


from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client

from .models import Notification, NotificationLog

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def send_notification(email, title, message):
        try:
            send_mail(
                subject=title,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return True, None
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return False, str(e)


class SMSService:
    def __init__(self):
        self.twilio_client = Client(
            getattr(settings, 'TWILIO_ACCOUNT_SID', ''),
            getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        )

    def send_notification(self, phone, message):
        try:
            if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
                return False, "SMS service not configured"

            self.twilio_client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone
            )
            return True, None
        except Exception as e:
            logger.error(f"SMS sending failed: {str(e)}")
            return False, str(e)


class TelegramService:
    @staticmethod
    def send_notification(chat_id, message):
        try:
            bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
            if not bot_token:
                return False, "Telegram bot token not configured"

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }

            response = requests.post(url, json=payload)
            if response.status_code == 200:
                return True, None
            else:
                return False, f"Telegram API error: {response.text}"
        except Exception as e:
            logger.error(f"Telegram sending failed: {str(e)}")
            return False, str(e)


class NotificationService:
    def __init__(self):
        self.email_service = EmailService()
        self.sms_service = SMSService()
        self.telegram_service = TelegramService()

    def get_user_channels(self, user):
        """Получить активные каналы пользователя в порядке приоритета"""
        return NotificationPreference.objects.filter(
            user=user, 
            is_active=True
        ).order_by('priority')

    def send_via_channel(self, channel, title, message):
        """Отправить уведомление через конкретный канал"""
        if channel.notification_type == 'email' and channel.email:
            return self.email_service.send_notification(channel.email, title, message)
        elif channel.notification_type == 'sms' and channel.phone:
            return self.sms_service.send_notification(channel.phone, message)
        elif channel.notification_type == 'telegram' and channel.telegram_chat_id:
            return self.telegram_service.send_notification(channel.telegram_chat_id, message)
        return False, "Channel not properly configured"

    def send_notification(self, user, title, message, preferred_channel=None):
        """Основной метод отправки уведомления с резервными каналами"""

        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=preferred_channel or 'email'
        )

        channels = self.get_user_channels(user)
        if not channels:
            notification.status = 'failed'
            notification.save()
            return False, "No active notification channels found"

        if preferred_channel:
            channels = sorted(channels, 
                            key=lambda x: x.notification_type != preferred_channel)

        success = False
        last_error = None

        for channel in channels:
            notification.retry_count += 1
            notification.save()

            log_entry = NotificationLog.objects.create(
                notification=notification,
                attempt_number=notification.retry_count,
                channel_used=channel.notification_type,
                status='pending'
            )

            try:
                success, error = self.send_via_channel(channel, title, message)

                if success:
                    log_entry.status = 'sent'
                    log_entry.save()

                    notification.status = 'sent'
                    notification.sent_at = timezone.now()
                    notification.notification_type = channel.notification_type
                    notification.save()
                    return True, None
                else:
                    log_entry.status = 'failed'
                    log_entry.error_message = error
                    log_entry.save()
                    last_error = error

            except Exception as e:
                logger.error(f"Error sending via {channel.notification_type}: {str(e)}")
                log_entry.status = 'failed'
                log_entry.error_message = str(e)
                log_entry.save()
                last_error = str(e)

        notification.status = 'failed'
        notification.save()
        return False, last_error or "All notification channels failed"
