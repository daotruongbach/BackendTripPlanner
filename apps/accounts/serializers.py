# apps/accounts/serializers.py
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import CustomerType  # sửa import cho đúng app của bạn

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    customer_type = serializers.ChoiceField(
        choices=CustomerType.choices, required=False, allow_null=True
    )

    class Meta:
        model = User
        fields = (
            "email", "password", "first_name", "last_name",
            "date_of_birth", "is_student", "customer_type",
        )

    def validate_email(self, value):
        value = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email đã tồn tại.")
        return value

    def validate(self, attrs):
        # 1) Độ mạnh mật khẩu
        validate_password(attrs.get("password"))

        # 2) Cross-field validation bằng model.clean()
        tmp = User(
            email=attrs.get("email"),
            first_name=attrs.get("first_name"),
            last_name=attrs.get("last_name"),
            date_of_birth=attrs.get("date_of_birth"),
            is_student=attrs.get("is_student", False),
            customer_type=attrs.get("customer_type", None),
            username=attrs.get("email"),  # đề phòng form/serializer bỏ trống
        )
        # clean() sẽ enforce quy tắc tuổi/HSSV nếu customer_type đã set
        tmp.full_clean(exclude=["password"])
        return attrs

    def create(self, validated_data):
        # Dùng manager để set username=email + hash password 1 lần
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class MeSerializer(serializers.ModelSerializer):
    customer_type = serializers.ChoiceField(
        choices=CustomerType.choices, required=False, allow_null=True
    )

    class Meta:
        model = User
        fields = (
            "email", "first_name", "last_name",
            "date_of_birth", "is_student", "customer_type",
            "age",
        )
        read_only_fields = ("email", "age")

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            setattr(instance, k, v)
        # Gọi model.clean() trước khi lưu để bắt sai logic
        instance.full_clean()
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_new_password(self, value):
        validate_password(value)
        return value
