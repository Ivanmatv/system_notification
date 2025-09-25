from rest_framework import serializers

from .models import NotificationLog


class SendSingleMessageSerializer(serializers.Serializer):
    """Сериализатор для отправки сообщения одному пользователю"""

    title = serializers.CharField(max_length=200)
    message = serializers.CharField()
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=20, required=False)
    telegram_chat_id = serializers.CharField(max_length=100, required=False)
    preferred_channel = serializers.ChoiceField(
        choices=NotificationLog.Channel.CHOICES,
        required=False
    )

    def validate(self, attrs):
        if not any([attrs.get('email'), attrs.get('phone'), attrs.get('telegram_chat_id')]):
            raise serializers.ValidationError(
                "Укажите хотя бы один контакт (email, phone или telegram_chat_id)"
            )
        return attrs


class SendBulkMessageSerializer(serializers.Serializer):
    """Сериализатор для отправки сообщения нескольким пользователям"""

    title = serializers.CharField(max_length=200)
    message = serializers.CharField()
    emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        default=[]
    )
    phones = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False,
        default=[]
    )
    telegram_chat_ids = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=[]
    )
    preferred_channel = serializers.ChoiceField(
        choices=NotificationLog.Channel.CHOICES,
        required=False
    )

    def validate(self, attrs):
        if not any([attrs.get('emails'), attrs.get('phones'), attrs.get('telegram_chat_ids')]):
            raise serializers.ValidationError(
                "Укажите хотя бы один список контактов (emails, phones или telegram_chat_ids)"
            )
        return attrs


class SendUserListMessageSerializer(serializers.Serializer):
    """Сериализатор для отправки сообщения списку пользователей"""

    title = serializers.CharField(max_length=200)
    message = serializers.CharField()
    users = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        help_text="Список пользователей: [{'email': '...', 'phone': '...', 'telegram_chat_id': '...'}]"
    )
    preferred_channel = serializers.ChoiceField(
        choices=NotificationLog.Channel.CHOICES,
        required=False
    )

    def validate_users(self, value):
        for user in value:
            if not any([user.get('email'), user.get('phone'), user.get('telegram_chat_id')]):
                raise serializers.ValidationError(
                    "Каждый пользователь должен иметь хотя бы один контакт"
                )
        return value


class NotificationLogSerializer(serializers.ModelSerializer):
    """Сериализатор для логирования результатов отправки сообщений"""
    channel_display = serializers.CharField(source='get_channel_used_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = NotificationLog
        fields = [
            'id', 'email', 'phone', 'telegram_chat_id', 'title', 'message',
            'channel_used', 'channel_display', 'status', 'status_display',
            'error_message', 'created_at'
        ]
        read_only_fields = fields


class BulkSendResultSerializer(serializers.Serializer):
    """Сериализатор для результатов массовой отправки"""

    total_recipients = serializers.IntegerField()
    successful = serializers.IntegerField()
    failed = serializers.IntegerField()
    details = serializers.ListField(child=serializers.DictField())