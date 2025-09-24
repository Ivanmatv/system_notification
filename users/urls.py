from django.urls import path, include

urlpatterns = [
    path('register/', UserViewSet.as_view({'post': 'register'}), name='register'),
    path('profile/', UserViewSet.as_view({'get': 'profile'}), name='profile'),
    path('auth/login/', AuthView.as_view(), name='login'),
]