import requests
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class SMSRuSimpleService:
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