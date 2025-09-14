from django.urls import path
from .views import (
    RegisterView, MeView, ChangePasswordView,
    PasswordResetRequestView, PasswordResetConfirmView,
    EmailTokenObtainPairView,
    AdminCreateUserView, SetRoleView,
)
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("me/", MeView.as_view()),
    path("change-password/", ChangePasswordView.as_view()),
    path("password-reset-request/", PasswordResetRequestView.as_view()),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view()),

    # JWT
    path("token/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    # Admin quản lý user
    path("admin/create-user/", AdminCreateUserView.as_view()),
    path("admin/set-role/<int:user_id>/", SetRoleView.as_view()),
]
