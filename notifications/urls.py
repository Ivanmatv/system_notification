from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationView, NotificationAsyncView, NotificationLogViewSet

router = DefaultRouter()
router.register(r'logs', NotificationLogViewSet, basename='log')

urlpatterns = [
    path('v1/send/', NotificationView.as_view(), name='send-message'),
    path('v1/send-async/', NotificationAsyncView.as_view(), name='send-message-async'),
    path('v1/', include(router.urls)),
]