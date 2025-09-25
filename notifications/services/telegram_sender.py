import requests
import logging

from django.conf import settings
from .base import BaseSender


logger = logging.getLogger(__name__)


class TelegramSender(BaseSender):
    """Отправка сообщений в telegram"""
    def send(self, destination, title, message):
        try:
            self.validate_destination(destination)

            bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
            if not bot_token:
                return False, "Токен бота Telegram не настроен"

            formatted_message = f"*{title}*\n{message}" if title else message

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': destination,
                'text': formatted_message,
                'parse_mode': 'Markdown'
            }

            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get('ok'):
                return True, None
            else:
                return False, f"Telegram API ошибка: {data.get('description', 'Unknown error')}"

        except Exception as e:
            logger.error(f"Telegram отправка не удалась {destination}: {str(e)}")
            return False, str(e)