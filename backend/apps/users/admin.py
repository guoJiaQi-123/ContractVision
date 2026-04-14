from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'phone', 'company_name', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'phone', 'company_name']
    ordering = ['-created_at']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('扩展信息', {'fields': ('phone', 'company_name', 'role', 'avatar')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('扩展信息', {'fields': ('phone', 'company_name', 'role')}),
    )
