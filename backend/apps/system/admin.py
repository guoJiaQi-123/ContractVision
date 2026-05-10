from django.contrib import admin

from .models import OperationLog


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'action', 'category', 'level', 'target', 'method', 'status_code', 'duration_ms', 'module', 'created_at']
    list_filter = ['category', 'level', 'action', 'method', 'status_code', 'module', 'created_at']
    search_fields = ['user__username', 'ip_address', 'target', 'detail', 'path']
    ordering = ['-created_at']
    readonly_fields = [
        'user', 'ip_address', 'action', 'category', 'level', 'target', 'detail',
        'before_data', 'after_data', 'method', 'path', 'status_code',
        'duration_ms', 'user_agent', 'module', 'created_at',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
