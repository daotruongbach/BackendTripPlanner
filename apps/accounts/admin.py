from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, Role

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = ("id", "email", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active")
    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Thông tin cá nhân", {"fields": ("first_name", "last_name", "date_of_birth", "is_student", "customer_type")}),
        ("Vai trò & quyền", {"fields": ("role", "groups", "user_permissions")}),
        ("Mốc thời gian", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "role", "is_active"),
        }),
    )

    # Ẩn 2 cờ để tránh sửa tay sai lệch; đã tự đồng bộ theo role
    readonly_fields = ("last_login", "date_joined")
