from django.contrib import admin

from .models import Contract, ContractChangeLog, PaymentPlan


class PaymentPlanInline(admin.TabularInline):
    model = PaymentPlan
    extra = 0


class ContractChangeLogInline(admin.TabularInline):
    model = ContractChangeLog
    extra = 0
    readonly_fields = ['field_name', 'old_value', 'new_value', 'changed_by', 'created_at']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = [
        'contract_no', 'title', 'client_name', 'amount', 'status',
        'payment_status', 'salesperson', 'sign_date', 'created_at',
    ]
    list_filter = ['status', 'payment_status', 'delivery_status', 'region', 'department']
    search_fields = ['contract_no', 'title', 'client_name', 'salesperson']
    ordering = ['-created_at']
    inlines = [PaymentPlanInline, ContractChangeLogInline]
    readonly_fields = ['created_at', 'updated_at', 'created_by']


@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = ['contract', 'phase', 'amount', 'due_date', 'status']
    list_filter = ['status']


@admin.register(ContractChangeLog)
class ContractChangeLogAdmin(admin.ModelAdmin):
    list_display = ['contract', 'field_name', 'changed_by', 'created_at']
    list_filter = ['field_name']
    readonly_fields = ['contract', 'field_name', 'old_value', 'new_value', 'changed_by', 'created_at']
