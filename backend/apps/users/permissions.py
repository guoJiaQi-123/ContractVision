from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    message = '仅管理员可执行此操作'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'admin'
        )


class IsOperator(BasePermission):
    message = '仅操作员及以上角色可执行此操作'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ('admin', 'operator')
        )


class IsViewer(BasePermission):
    message = '需要登录后才能查看'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ('admin', 'operator', 'viewer')
        )
