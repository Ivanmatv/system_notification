import logging
import requests

from django.conf import settings

from .base import BaseSender


logger = logging.getLogger(__name__)


class SMSSender(BaseSender):
    """Отправка сообщений по sms"""
    def send(self, destination, title, message):
        try:
            self.validate_destination(destination)

            api_id = getattr(settings, 'SMSRU_API_ID', '')
            if not api_id:
                return False, "Служба SMS не настроена"

            sms_message = f"{title}: {message}" if title else message

            url = "https://sms.ru/sms/send"
            params = {
                'api_id': api_id,
                'to': destination,
                'msg': sms_message,
                'json': 1
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get('status') == 'OK':
                return True, None
            else:
                return False, f"SMS ошибка: {data.get('status_text', 'Unknown error')}"

        except Exception as e:
            logger.error(f"Отправка СМС не удалась {destination}: {str(e)}")
            return False, str(e)