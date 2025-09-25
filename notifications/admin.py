from django.contrib import admin

from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'channel_used', 'status', 'email', 'phone', 'created_at']
    list_filter = ['channel_used', 'status', 'created_at']
    search_fields = ['title', 'message', 'email', 'phone', 'telegram_chat_id']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False