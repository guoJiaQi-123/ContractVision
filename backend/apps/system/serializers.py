from rest_framework import serializers

from .models import (
    AlertMessage,
    AlertRule,
    CurrencyRate,
    DashboardConfig,
    DataPermissionRule,
    DataTemplate,
    IntegrationConfig,
    OperationLog,
    SalesTarget,
    StampTaxRule,
)


class OperationLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default='')

    class Meta:
        model = OperationLog
        fields = [
            'id', 'user', 'username', 'ip_address', 'action',
            'target', 'detail', 'before_data', 'after_data', 'method', 'path',
            'status_code', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class IntegrationConfigSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = IntegrationConfig
        fields = [
            'id', 'name', 'system_type', 'api_url', 'auth_type',
            'auth_config', 'field_mapping', 'sync_interval',
            'status', 'status_display', 'last_sync_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_sync_at']


class DataPermissionRuleSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default='')

    class Meta:
        model = DataPermissionRule
        fields = [
            'id', 'user', 'username', 'scope_type', 'scope_value',
            'can_edit', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AlertRuleSerializer(serializers.ModelSerializer):
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)

    class Meta:
        model = AlertRule
        fields = [
            'id', 'name', 'rule_type', 'rule_type_display',
            'remind_days', 'owner_role', 'level', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AlertMessageSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.username', read_only=True, default='')
    processed_by_name = serializers.CharField(source='processed_by.username', read_only=True, default='')
    contract_no = serializers.CharField(source='contract.contract_no', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AlertMessage
        fields = [
            'id', 'contract', 'contract_no', 'rule',
            'title', 'content', 'warning_type', 'level',
            'owner', 'owner_name', 'due_date',
            'status', 'status_display',
            'processed_by', 'processed_by_name', 'processed_at',
            'created_at',
        ]
        read_only_fields = ['id', 'processed_by', 'processed_at', 'created_at']


class SalesTargetSerializer(serializers.ModelSerializer):
    target_type_display = serializers.CharField(source='get_target_type_display', read_only=True)
    period_type_display = serializers.CharField(source='get_period_type_display', read_only=True)

    class Meta:
        model = SalesTarget
        fields = [
            'id', 'name', 'target_type', 'target_type_display',
            'owner_value', 'period_type', 'period_type_display',
            'period_label', 'start_date', 'end_date',
            'target_amount', 'warning_threshold',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DashboardConfigSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default='')

    class Meta:
        model = DashboardConfig
        fields = [
            'id', 'name', 'role_scope', 'layout', 'widgets',
            'is_mobile', 'is_active', 'created_by', 'created_by_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class DataTemplateSerializer(serializers.ModelSerializer):
    template_type_display = serializers.CharField(source='get_template_type_display', read_only=True)

    class Meta:
        model = DataTemplate
        fields = [
            'id', 'name', 'template_type', 'template_type_display',
            'version', 'field_config', 'validation_rules',
            'is_active', 'description', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CurrencyRateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CurrencyRate
        fields = [
            'id', 'currency', 'base_currency', 'rate',
            'effective_date', 'is_latest', 'remark',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StampTaxRuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = StampTaxRule
        fields = [
            'id', 'contract_type', 'rate', 'description',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
