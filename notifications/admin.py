from django.contrib import admin
from .models import Notification, NotificationPreference, NotificationLog


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'status', 'created_at']
    list_filter = ['status', 'notification_type', 'created_at']
    search_fields = ['title', 'message', 'user__username']


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'is_active', 'priority']
    list_filter = ['notification_type', 'is_active']


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['notification', 'attempt_number', 'channel_used', 'status', 'created_at']
    list_filter = ['channel_used', 'status']


admin.site.site_header = "Notification System Admin"