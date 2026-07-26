from rest_framework import permissions


class QuestionListPermission(permissions.BasePermission):
    """List permissions: public reads, administrator writes, owner deletion."""

    def has_permission(self, request, view) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return obj.can_view(request.user)
        if request.method == "DELETE":
            return obj.owner_id == request.user.id
        return obj.can_administer(request.user)
