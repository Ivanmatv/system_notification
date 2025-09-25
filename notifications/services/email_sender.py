import logging

from django.core.mail import send_mail
from django.conf import settings
from .base import BaseSender


logger = logging.getLogger(__name__)


class EmailSender(BaseSender):
    """Отправка сообщений по почте"""
    def send(self, destination, title, message):
        try:
            self.validate_destination(destination)

            send_mail(
                subject=title,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destination],
                fail_silently=False,
            )
            return True, None

        except Exception as e:
            logger.error(f"Не удалось отправить электронное письмо {destination}: {str(e)}")
            return False, str(e)