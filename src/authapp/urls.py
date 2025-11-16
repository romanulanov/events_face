from django.urls import path

from .views import (LoginAPIView, LogoutAPIView, RegisterAPIView,
                    TokenRefreshCustomView)

urlpatterns = [
    path("register", RegisterAPIView.as_view(), name="auth-register"),
    path("login", LoginAPIView.as_view(), name="auth-login"),
    path("token/refresh", TokenRefreshCustomView.as_view(), name="token-\
         refresh"),
    path("logout", LogoutAPIView.as_view(), name="auth-logout"),
]
