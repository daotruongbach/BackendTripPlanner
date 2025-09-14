from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import Role

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user_id = getattr(request.user, "id", None)
        owner_id = (
            getattr(obj, "user_id", None)
            or getattr(obj, "owner_id", None)
            or getattr(getattr(obj, "user", None), "id", None)
            or getattr(getattr(obj, "owner", None), "id", None)
        )
        return owner_id == user_id

class MinRole(BasePermission):
    required_role = Role.USER

    @classmethod
    def at_least(cls, role):
        class _P(cls):
            required_role = role
        return _P

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.has_role_at_least(self.required_role))
