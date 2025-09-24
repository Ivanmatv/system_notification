from celery import shared_task
from django.contrib.auth.models import User
from .services.notification_services import NotificationService


@shared_task(bind=True, max_retries=3)
def send_notification_task(self, user_id, title, message, preferred_channel=None):
    try:
        user = User.objects.get(id=user_id)
        service = NotificationService()
        success, error = service.send_notification(user, title, message, preferred_channel)

        if not success:
            # Повторная попытка через Celery
            raise Exception(error)

        return {'status': 'success', 'message': 'Notification sent'}

    except Exception as exc:
        self.retry(exc=exc, countdown=60)  # Повтор через 60 секунд