from django.urls import path
from .views import ApiRegisterView, ApiLoginView
from rest_framework_simplejwt.views import TokenRefreshView

# API endpoints for authentication
urlpatterns = [
    path('register/', ApiRegisterView.as_view(), name='api_register'),
    path('login/', ApiLoginView.as_view(), name='api_login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]