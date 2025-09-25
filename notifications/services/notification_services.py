import logging
from typing import List, Tuple

from .email_sender import EmailSender
from .sms_sender import SMSSender
from .telegram_sender import TelegramSender
from ..models import NotificationLog, ChannelConfig


logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис отправки уведомлений нескольким пользователям"""

    def __init__(self):
        self.senders = {
            'email': EmailSender(),
            'sms': SMSSender(),
            'telegram': TelegramSender(),
        }
        self.channel_priority = ['telegram', 'email', 'sms']

    def send_single_message(self, title: str, message: str,
                          email: str = None, phone: str = None,
                          telegram_chat_id: str = None,
                          preferred_channel: str = None) -> Tuple[bool, str]:
        """Отправить сообщение одному пользователю"""
        config = ChannelConfig(
            emails=[email] if email else [],
            phones=[phone] if phone else [],
            telegram_chat_ids=[telegram_chat_id] if telegram_chat_id else []
        )

        return self._send_to_channels(title, message, config, preferred_channel, single_recipient=True)

    def send_bulk_message(self, title: str, message: str,
                         emails: List[str] = None, phones: List[str] = None,
                         telegram_chat_ids: List[str] = None,
                         preferred_channel: str = None) -> dict:
        """Отправить сообщение нескольким пользователям"""
        config = ChannelConfig(
            emails=emails or [],
            phones=phones or [],
            telegram_chat_ids=telegram_chat_ids or []
        )

        results = {
            'total_recipients': len(emails or []) + len(phones or []) + len(telegram_chat_ids or []),
            'successful': 0,
            'failed': 0,
            'details': []
        }

        # Отправляем на все email
        for email in config.emails:
            success, message_result = self._send_to_single_contact(
                title, message, 'email', email, preferred_channel
            )
            results['details'].append({
                'contact': email,
                'channel': 'email',
                'success': success,
                'message': message_result
            })
            if success:
                results['successful'] += 1
            else:
                results['failed'] += 1

        # Отправляем на все телефоны
        for phone in config.phones:
            success, message_result = self._send_to_single_contact(
                title, message, 'sms', phone, preferred_channel
            )
            results['details'].append({
                'contact': phone,
                'channel': 'sms',
                'success': success,
                'message': message_result
            })
            if success:
                results['successful'] += 1
            else:
                results['failed'] += 1

        # Отправляем на все Telegram chat_id
        for chat_id in config.telegram_chat_ids:
            success, message_result = self._send_to_single_contact(
                title, message, 'telegram', chat_id, preferred_channel
            )
            results['details'].append({
                'contact': chat_id,
                'channel': 'telegram',
                'success': success,
                'message': message_result
            })
            if success:
                results['successful'] += 1
            else:
                results['failed'] += 1

        return results

    def _send_to_single_contact(self, title: str, message: str, channel: str, 
                              destination: str, preferred_channel: str = None) -> Tuple[bool, str]:
        """Отправить сообщение одному контакту через указанный канал"""
        try:
            sender = self.senders.get(channel)
            if not sender:
                return False, f"Unsupported channel: {channel}"

            success, error = sender.send(destination, title, message)

            log_data = {
                'email': destination if channel == 'email' else None,
                'phone': destination if channel == 'sms' else None,
                'telegram_chat_id': destination if channel == 'telegram' else None,
            }

            NotificationLog.create_log(
                channel_used=channel,
                status=NotificationLog.Status.SENT if success else NotificationLog.Status.FAILED,
                title=title,
                message=message,
                error_message=error if not success else None,
                **log_data
            )

            if success:
                return True, f"Сообщение отправлено на {destination} через {channel}"
            else:
                return False, f"Ошибка отправки на {destination} через {channel}: {error}"

        except Exception as e:
            logger.error(f"Error sending to {destination} via {channel}: {str(e)}")
            return False, str(e)

    def _send_to_channels(self, title: str, message: str, config: ChannelConfig,
                         preferred_channel: str = None, single_recipient: bool = False) -> Tuple[bool, str]:
        """ Отправка с через разные каналы (для одного пользователя)"""
        channels_to_try = self.channel_priority.copy()
        if preferred_channel and preferred_channel in channels_to_try:
            channels_to_try.remove(preferred_channel)
            channels_to_try.insert(0, preferred_channel)

        last_error = None

        for channel in channels_to_try:
            destinations = []
            if channel == 'email' and config.emails:
                destinations = config.emails
            elif channel == 'sms' and config.phones:
                destinations = config.phones
            elif channel == 'telegram' and config.telegram_chat_ids:
                destinations = config.telegram_chat_ids

            if not destinations:
                continue

            # Для одного пользователя берем первый доступный контакт
            destination = destinations[0] if single_recipient else None
            if single_recipient:
                success, result = self._send_to_single_contact(
                    title, message, channel, destination, preferred_channel
                )
                if success:
                    return True, result
                last_error = result
            else:
                # Для множественных получателей пробуем все каналы
                for dest in destinations:
                    success, result = self._send_to_single_contact(
                        title, message, channel, dest, preferred_channel
                    )
                    if success and single_recipient:
                        return True, result
                    if not success:
                        last_error = result

        return False, last_error or "Не удалось отправить сообщение"