# permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    """
    Cho phép GET/HEAD/OPTIONS; còn lại thì phải là chủ sở hữu.
    Hỗ trợ obj.user, obj.user_id, obj.owner, obj.owner_id.
    """
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
