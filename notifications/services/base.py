import logging

from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseSender(ABC):
    """Абстрактный базовый класс для отправщиков"""

    @abstractmethod
    def send(self, destination, title, message):
        """Отправить сообщение"""
        pass

    def validate_destination(self, destination):
        """Валидация адреса назначения"""
        if not destination:
            raise ValueError("Пункт назначения не может быть пустым")
        return True