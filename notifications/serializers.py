from rest_framework import serializers

from .models import Notification, NotificationPreference
from users.serializers import UserSerializer


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ['id', 'user', 'notification_type', 'is_active', 'priority', 
                 'email', 'phone', 'telegram_chat_id']
        read_only_fields = ['user']


class NotificationSerializer(serializers.ModelSerializer):
    user_info = UserSerializer(source='user', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'user', 'user_info', 'title', 'message', 'notification_type',
                 'status', 'created_at', 'sent_at', 'retry_count', 'max_retries']
        read_only_fields = ['status', 'created_at', 'sent_at', 'retry_count']


class SendNotificationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    title = serializers.CharField(max_length=200)
    message = serializers.CharField()
    preferred_channel = serializers.ChoiceField(
        choices=NotificationPreference.NOTIFICATION_TYPES,
        required=False
    )
