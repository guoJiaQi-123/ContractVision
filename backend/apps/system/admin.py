from django.contrib import admin

from .models import OperationLog


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'action', 'target', 'method', 'status_code', 'created_at']
    list_filter = ['action', 'method', 'status_code', 'created_at']
    search_fields = ['user__username', 'ip_address', 'target', 'detail']
    ordering = ['-created_at']
    readonly_fields = [
        'user', 'ip_address', 'action', 'target', 'detail',
        'method', 'path', 'status_code', 'created_at',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
