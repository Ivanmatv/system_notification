from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import NotificationLog
from .serializers import (
    SendSingleMessageSerializer, 
    SendBulkMessageSerializer,
    SendUserListMessageSerializer,
    NotificationLogSerializer,
    BulkSendResultSerializer
)
from .services.notification_service import NotificationService
from .tasks import send_single_message_task, send_bulk_message_task


class NotificationView(APIView):
    """API для отправки сообщений одному или нескольким пользователям"""

    def post(self, request):
        """Отправить сообщение (автоопределение типа отправки)"""
        if any(key in request.data for key in ['emails', 'phones', 'telegram_chat_ids']):
            return self._send_bulk(request)
        elif 'users' in request.data:
            return self._send_user_list(request)
        else:
            return self._send_single(request)

    def _send_single(self, request):
        """Отправить сообщение одному пользователю"""
        serializer = SendSingleMessageSerializer(data=request.data)

        if serializer.is_valid():
            service = NotificationService()

            success, result_message = service.send_single_message(
                title=serializer.validated_data['title'],
                message=serializer.validated_data['message'],
                email=serializer.validated_data.get('email'),
                phone=serializer.validated_data.get('phone'),
                telegram_chat_id=serializer.validated_data.get('telegram_chat_id'),
                preferred_channel=serializer.validated_data.get('preferred_channel')
            )

            if success:
                return Response({
                    'status': 'success',
                    'message': result_message,
                    'type': 'single'
                })
            else:
                return Response({
                    'status': 'error',
                    'message': result_message,
                    'type': 'single'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _send_bulk(self, request):
        """Отправить сообщение нескольким пользователям по спискам контактов"""
        serializer = SendBulkMessageSerializer(data=request.data)

        if serializer.is_valid():
            service = NotificationService()

            results = service.send_bulk_message(
                title=serializer.validated_data['title'],
                message=serializer.validated_data['message'],
                emails=serializer.validated_data.get('emails', []),
                phones=serializer.validated_data.get('phones', []),
                telegram_chat_ids=serializer.validated_data.get('telegram_chat_ids', []),
                preferred_channel=serializer.validated_data.get('preferred_channel')
            )

            result_serializer = BulkSendResultSerializer(results)
            return Response({
                'status': 'success',
                'type': 'bulk',
                'results': result_serializer.data
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _send_user_list(self, request):
        """Отправить сообщение списку пользователей"""
        serializer = SendUserListMessageSerializer(data=request.data)

        if serializer.is_valid():

            emails = []
            phones = []
            telegram_chat_ids = []

            for user in serializer.validated_data['users']:
                if user.get('email'):
                    emails.append(user['email'])
                if user.get('phone'):
                    phones.append(user['phone'])
                if user.get('telegram_chat_id'):
                    telegram_chat_ids.append(user['telegram_chat_id'])

            service = NotificationService()
            results = service.send_bulk_message(
                title=serializer.validated_data['title'],
                message=serializer.validated_data['message'],
                emails=emails,
                phones=phones,
                telegram_chat_ids=telegram_chat_ids,
                preferred_channel=serializer.validated_data.get('preferred_channel')
            )

            result_serializer = BulkSendResultSerializer(results)
            return Response({
                'status': 'success',
                'type': 'user_list',
                'results': result_serializer.data
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationAsyncView(APIView):
    """Асинхронная отправка сообщений"""

    def post(self, request):
        """Асинхронная отправка сообщения"""
        if any(key in request.data for key in ['emails', 'phones', 'telegram_chat_ids']):
            # Массовая отправка
            task = send_bulk_message_task.delay(
                title=request.data['title'],
                message=request.data['message'],
                emails=request.data.get('emails', []),
                phones=request.data.get('phones', []),
                telegram_chat_ids=request.data.get('telegram_chat_ids', []),
                preferred_channel=request.data.get('preferred_channel')
            )
        else:
            # Отправка одному пользователю
            task = send_single_message_task.delay(
                title=request.data['title'],
                message=request.data['message'],
                email=request.data.get('email'),
                phone=request.data.get('phone'),
                telegram_chat_id=request.data.get('telegram_chat_id'),
                preferred_channel=request.data.get('preferred_channel')
            )

        return Response({
            'status': 'queued',
            'task_id': task.id,
            'message': 'Сообщение поставлено в очередь на отправку'
        })


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр логов отправки сообщений"""
    queryset = NotificationLog.objects.all()
    serializer_class = NotificationLogSerializer

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Статистика отправки"""
        stats = {
            'total': NotificationLog.objects.count(),
            'sent': NotificationLog.objects.filter(status=NotificationLog.Status.SENT).count(),
            'failed': NotificationLog.objects.filter(status=NotificationLog.Status.FAILED).count(),
            'by_channel': {
                'email': {
                    'total': NotificationLog.objects.filter(channel_used='email').count(),
                    'sent': NotificationLog.objects.filter(channel_used='email', status='sent').count(),
                    'failed': NotificationLog.objects.filter(channel_used='email', status='failed').count(),
                },
                'sms': {
                    'total': NotificationLog.objects.filter(channel_used='sms').count(),
                    'sent': NotificationLog.objects.filter(channel_used='sms', status='sent').count(),
                    'failed': NotificationLog.objects.filter(channel_used='sms', status='failed').count(),
                },
                'telegram': {
                    'total': NotificationLog.objects.filter(channel_used='telegram').count(),
                    'sent': NotificationLog.objects.filter(channel_used='telegram', status='sent').count(),
                    'failed': NotificationLog.objects.filter(channel_used='telegram', status='failed').count(),
                }
            }
        }
        return Response(stats)