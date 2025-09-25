import logging

from celery import shared_task

from .services.notification_service import NotificationService

logger = logging.getLogger(__name__)


@shared_task
def send_single_message_task(
    title,
    message,
    email=None,
    phone=None,
    telegram_chat_id=None,
    preferred_channel=None
):
    """Асинхронная отправка сообщения одному пользователю"""
    try:
        service = NotificationService()
        success, result = service.send_single_message(
            title=title,
            message=message,
            email=email,
            phone=phone,
            telegram_chat_id=telegram_chat_id,
            preferred_channel=preferred_channel
        )

        return {
            'status': 'success' if success else 'error',
            'message': result,
            'type': 'single'
        }

    except Exception as e:
        logger.error(f"Error in send_single_message_task: {str(e)}")
        return {
            'status': 'error',
            'message': str(e),
            'type': 'single'
        }


@shared_task
def send_bulk_message_task(
    title,
    message,
    emails=None,
    phones=None,
    telegram_chat_ids=None,
    preferred_channel=None
):
    """Асинхронная массовая отправка сообщений"""
    try:
        service = NotificationService()
        results = service.send_bulk_message(
            title=title,
            message=message,
            emails=emails or [],
            phones=phones or [],
            telegram_chat_ids=telegram_chat_ids or [],
            preferred_channel=preferred_channel
        )

        return {
            'status': 'success',
            'results': results,
            'type': 'bulk'
        }

    except Exception as e:
        logger.error(f"Error in send_bulk_message_task: {str(e)}")
        return {
            'status': 'error',
            'message': str(e),
            'type': 'bulk'
        }