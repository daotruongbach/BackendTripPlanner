# apps/accounts/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, MeView, ChangePasswordView,
    PasswordResetRequestView, PasswordResetConfirmView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", TokenObtainPairView.as_view(), name="auth-login"),  # nhận 'email' + 'password'
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    path("me/", MeView.as_view(), name="auth-me"),
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),

    path("password-reset/", PasswordResetRequestView.as_view(), name="auth-password-reset"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="auth-password-reset-confirm"),
]
