# notifications/tasks.py
from celery import shared_task
from django.contrib.auth.models import User
from .services.notification_services import NotificationService
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_notification_task(self, user_id, title, message, preferred_channel=None):
    try:
        user = User.objects.get(id=user_id)
        service = NotificationService()
        success, error = service.send_notification(user, title, message, preferred_channel)

        if not success:
            logger.error(f"Failed to send notification to user {user_id}: {error}")

            raise Exception(error)

        logger.info(f"Notification sent successfully to user {user_id}")
        return {
            'status': 'success', 
            'message': 'Notification sent',
            'user_id': user_id,
            'title': title
        }

    except User.DoesNotExist as exc:
        logger.error(f"User {user_id} not found")
        # Не повторяем попытку, если пользователь не найден
        return {'status': 'error', 'message': 'User not found'}

    except Exception as exc:
        logger.error(f"Error sending notification: {str(exc)}")
        # Повтор через 60 секунд
        self.retry(exc=exc, countdown=60)