from datetime import timezone
import logging
import requests

from django.core.mail import send_mail
from django.conf import settings
from notifications.models import NotificationPreference, Notification, NotificationLog

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


class TelegramService:
    def __init__(self):
        self.bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, chat_id, message, parse_mode='HTML'):
        """Отправка сообщения в Telegram"""
        try:
            if not self.bot_token:
                return False, "Telegram bot token not configured"

            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }

            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get('ok'):
                return True, None
            else:
                return False, f"Telegram API error: {data.get('description', 'Unknown error')}"

        except requests.exceptions.RequestException as e:
            logger.error(f"Telegram sending error: {str(e)}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Unexpected Telegram error: {str(e)}")
            return False, str(e)

    def get_bot_info(self):
        """Получение информации о боте"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=5)
            data = response.json()
            return data if data.get('ok') else None
        except Exception as e:
            logger.error(f"Bot info error: {str(e)}")
            return None


def get_telegram_chat_id(bot_token):
    """Получить chat_id через обновления бота"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url, timeout=5)
        data = response.json()

        if data.get('ok') and data.get('result'):
            for update in data['result']:
                if 'message' in update:
                    return update['message']['chat']['id']
        return None
    except Exception as e:
        logger.error(f"Chat ID fetch error: {str(e)}")
        return None


class SMSService:
    def send_sms(self, phone, message):
        """Простая отправка через SMS.ru API"""
        try:
            api_id = getattr(settings, 'SMSRU_API_ID', '')
            if not api_id:
                return False, "SMS API ID not configured"

            url = "https://sms.ru/sms/send"
            params = {
                'api_id': api_id,
                'to': phone,
                'msg': message,
                'json': 1
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get('status') == 'OK':
                return True, None
            else:
                return False, f"SMS error: {data.get('status_text', 'Unknown error')}"

        except Exception as e:
            logger.error(f"SMS sending error: {str(e)}")
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
