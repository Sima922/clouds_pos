from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsCashier(permissions.BasePermission):
    """
    Allows access only to cashier users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'cashier'