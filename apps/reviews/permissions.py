from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.accounts.models import Role

class IsOwnerOrStaffCanDelete(BasePermission):
    """DELETE: owner hoặc staff/admin. PUT/PATCH chặn với user thường."""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.method == "DELETE":
            if not request.user.is_authenticated:
                return False
            return (obj.user_id == request.user.id) or int(getattr(request.user, "role", 1)) >= int(Role.STAFF)
        # PUT/PATCH chỉ cho staff trở lên
        return int(getattr(request.user, "role", 1)) >= int(Role.STAFF)