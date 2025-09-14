from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import CustomerType, Role

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    customer_type = serializers.ChoiceField(choices=CustomerType.choices, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name",
                  "date_of_birth", "is_student", "customer_type")

    def validate_email(self, value):
        value = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email đã tồn tại.")
        return value

    def validate(self, attrs):
        validate_password(attrs.get("password"))
        tmp = User(
            email=attrs.get("email"),
            first_name=attrs.get("first_name"),
            last_name=attrs.get("last_name"),
            date_of_birth=attrs.get("date_of_birth"),
            is_student=attrs.get("is_student", False),
            customer_type=attrs.get("customer_type", None),
            username=attrs.get("email"),
        )
        tmp.full_clean(exclude=["password"])
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        # luôn tạo User thường
        user = User.objects.create_user(password=password, **validated_data)
        return user

class AdminCreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    role = serializers.ChoiceField(choices=Role.choices)

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name",
                  "date_of_birth", "is_student", "customer_type", "role")

    def create(self, validated_data):
        pwd = validated_data.pop("password")
        return User.objects.create_user(password=pwd, **validated_data)

class SetRoleSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=Role.choices)

    class Meta:
        model = User
        fields = ("role",)

    def update(self, instance, validated_data):
        instance.role = validated_data["role"]
        instance.save()
        return instance

class MeSerializer(serializers.ModelSerializer):
    customer_type = serializers.ChoiceField(choices=CustomerType.choices, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name",
                  "date_of_birth", "is_student", "customer_type", "age", "role")
        read_only_fields = ("email", "age", "role")

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
