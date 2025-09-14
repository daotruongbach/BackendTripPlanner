from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    RegisterSerializer, MeSerializer, ChangePasswordSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    AdminCreateUserSerializer, SetRoleSerializer
)
from .permissions import MinRole
from .models import Role

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        return Response({"id": user.id, "email": user.email, "role": user.get_role_display()}, status=status.HTTP_201_CREATED)

class AdminCreateUserView(APIView):
    permission_classes = [permissions.IsAuthenticated, MinRole.at_least(Role.ADMIN)]
    def post(self, request):
        s = AdminCreateUserSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        u = s.save()
        return Response({"id": u.id, "email": u.email, "role": u.get_role_display()}, status=status.HTTP_201_CREATED)

class SetRoleView(APIView):
    permission_classes = [permissions.IsAuthenticated, MinRole.at_least(Role.ADMIN)]
    def post(self, request, user_id):
        try:
            u = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "Không tìm thấy user."}, status=status.HTTP_404_NOT_FOUND)
        s = SetRoleSerializer(u, data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return Response({"id": u.id, "email": u.email, "role": u.get_role_display()})

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        return Response(MeSerializer(request.user).data)
    def put(self, request):
        s = MeSerializer(request.user, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        s = ChangePasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(s.validated_data["old_password"]):
            return Response({"detail": "Mật khẩu cũ không đúng"}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(s.validated_data["new_password"])
        user.save()
        return Response({"detail": "Đổi mật khẩu thành công"})

class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = PasswordResetRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        email = s.validated_data["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Nếu email tồn tại, liên kết đặt lại sẽ được gửi."})
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"http://localhost:3000/reset-password?uid={uid}&token={token}"
        send_mail("Đặt lại mật khẩu", f"Nhấn để đặt lại: {reset_link}", from_email=None, recipient_list=[email])
        return Response({"detail": "Đã gửi email đặt lại mật khẩu (console backend)."})

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        s = PasswordResetConfirmSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            uid = urlsafe_base64_decode(s.validated_data["uidb64"]).decode()
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({"detail": "Liên kết không hợp lệ"}, status=status.HTTP_400_BAD_REQUEST)
        token = s.validated_data["token"]
        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Token không hợp lệ"}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(s.validated_data["new_password"])
        user.save()
        return Response({"detail": "Đặt lại mật khẩu thành công"})

# ==== JWT qua email ====
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"

class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
