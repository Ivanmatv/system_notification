import requests
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


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
