from rest_framework.views import APIView
from rest_framework.decorators import action


class UserViewSet(ViewSet):
    # API для работы с пользователями
    @action(detail=False, methods=['post'])
    def register(self, request):
        # Регистрация нового пользователя
        pass

    @action(detail=False, methods=['get'])
    def profile(self, request):
        # Получение профиля текущего пользователя
        pass

    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        # Обновление профиля
        pass
