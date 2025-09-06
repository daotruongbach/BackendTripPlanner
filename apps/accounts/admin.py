from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = ("id", "email", "first_name", "last_name", "is_staff", "is_superuser", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active")
    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name")
    # form hiển thị/sửa user
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Thông tin cá nhân", {"fields": ("first_name", "last_name")}),
        ("Quyền hạn", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Mốc thời gian", {"fields": ("last_login", "date_joined")}),
    )
    # form tạo user trong admin
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "is_staff", "is_superuser", "is_active"),
        }),
    )

