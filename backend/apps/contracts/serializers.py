from rest_framework import serializers

from .models import (
    ApprovalProcess,
    ApprovalRequest,
    Contract,
    ContractChangeLog,
    ContractChangeRequest,
    ContractMilestone,
    PaymentPlan,
)
from .services import compute_contract_progress, payment_overdue_meta, update_contract_metrics


class PaymentPlanSerializer(serializers.ModelSerializer):
    overdue_days = serializers.SerializerMethodField()
    overdue_level = serializers.SerializerMethodField()
    invoice_status_display = serializers.CharField(source='get_invoice_status_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PaymentPlan
        fields = [
            'id', 'phase', 'ratio', 'amount', 'actual_amount',
            'due_date', 'paid_date', 'status', 'status_display',
            'invoice_status', 'invoice_status_display',
            'voucher_no', 'remark', 'overdue_days', 'overdue_level',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_overdue_days(self, obj):
        return payment_overdue_meta(obj)['overdue_days']

    def get_overdue_level(self, obj):
        return payment_overdue_meta(obj)['overdue_level']


class ContractMilestoneSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    node_type_display = serializers.CharField(source='get_node_type_display', read_only=True)

    class Meta:
        model = ContractMilestone
        fields = [
            'id', 'contract', 'node_type', 'node_type_display',
            'name', 'progress_weight', 'planned_date', 'actual_date',
            'status', 'status_display', 'remark', 'evidences',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ContractChangeLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True, default='')

    class Meta:
        model = ContractChangeLog
        fields = [
            'id', 'field_name', 'old_value', 'new_value',
            'changed_by', 'changed_by_name', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ContractChangeRequestSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True, default='')
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    change_type_display = serializers.CharField(source='get_change_type_display', read_only=True)

    class Meta:
        model = ContractChangeRequest
        fields = [
            'id', 'contract', 'change_type', 'change_type_display',
            'title', 'reason', 'effective_date',
            'before_snapshot', 'after_snapshot', 'attachments',
            'status', 'status_display',
            'requested_by', 'requested_by_name',
            'approved_by', 'approved_by_name',
            'approved_at', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'before_snapshot', 'requested_by', 'approved_by',
            'approved_at', 'created_at', 'updated_at',
        ]


class ApprovalProcessSerializer(serializers.ModelSerializer):

    class Meta:
        model = ApprovalProcess
        fields = [
            'id', 'name', 'action_type', 'min_amount', 'steps',
            'is_active', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class ApprovalRequestSerializer(serializers.ModelSerializer):
    process_name = serializers.CharField(source='process.name', read_only=True, default='')
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True, default='')
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ApprovalRequest
        fields = [
            'id', 'contract', 'process', 'process_name',
            'action_type', 'title', 'request_payload',
            'status', 'status_display', 'current_step', 'review_logs',
            'requested_by', 'requested_by_name',
            'reviewed_by', 'reviewed_by_name',
            'reviewed_at', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'requested_by', 'reviewed_by', 'reviewed_at',
            'created_at', 'updated_at',
        ]


class ContractSerializer(serializers.ModelSerializer):
    payment_plans = PaymentPlanSerializer(many=True, read_only=True)
    change_logs = ContractChangeLogSerializer(many=True, read_only=True)
    milestones = ContractMilestoneSerializer(many=True, read_only=True)
    change_requests = ContractChangeRequestSerializer(many=True, read_only=True)
    approval_requests = ApprovalRequestSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default='')
    renewal_owner_name = serializers.CharField(source='renewal_owner.username', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    delivery_status_display = serializers.CharField(source='get_delivery_status_display', read_only=True)
    approval_status_display = serializers.CharField(source='get_approval_status_display', read_only=True)
    renewal_status_display = serializers.CharField(source='get_renewal_status_display', read_only=True)
    fulfillment_progress = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = [
            'id', 'contract_no', 'title', 'client_name', 'client_contact',
            'contract_type', 'product_type', 'amount', 'base_amount',
            'currency', 'region',
            'sign_date', 'start_date', 'end_date',
            'status', 'status_display',
            'payment_status', 'payment_status_display',
            'delivery_status', 'delivery_status_display',
            'approval_status', 'approval_status_display',
            'renewal_status', 'renewal_status_display',
            'renewal_reminder_days', 'renewal_contract_no',
            'salesperson', 'department', 'description', 'attachments',
            'quality_score', 'quality_issues',
            'stamp_tax_rate', 'stamp_tax_amount',
            'terminated_reason', 'terminated_at', 'termination_attachments',
            'created_by', 'created_by_name',
            'renewal_owner', 'renewal_owner_name',
            'created_at', 'updated_at',
            'payment_plans', 'milestones', 'change_logs',
            'change_requests', 'approval_requests', 'fulfillment_progress',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_fulfillment_progress(self, obj):
        return compute_contract_progress(obj)


class ContractCreateSerializer(serializers.ModelSerializer):
    payment_plans = PaymentPlanSerializer(many=True, required=False)
    milestones = ContractMilestoneSerializer(many=True, required=False)

    class Meta:
        model = Contract
        fields = [
            'contract_no', 'title', 'client_name', 'client_contact',
            'contract_type', 'product_type', 'amount', 'currency', 'region',
            'sign_date', 'start_date', 'end_date',
            'status', 'payment_status', 'delivery_status',
            'approval_status', 'renewal_status', 'renewal_reminder_days',
            'renewal_contract_no', 'renewal_owner',
            'salesperson', 'department', 'description', 'attachments',
            'terminated_reason', 'terminated_at', 'termination_attachments',
            'payment_plans', 'milestones',
        ]

    def create(self, validated_data):
        payment_plans_data = validated_data.pop('payment_plans', [])
        milestones_data = validated_data.pop('milestones', [])
        contract = Contract.objects.create(**validated_data)
        for plan_data in payment_plans_data:
            PaymentPlan.objects.create(contract=contract, **plan_data)
        for milestone_data in milestones_data:
            ContractMilestone.objects.create(contract=contract, **milestone_data)
        update_contract_metrics(contract)
        return contract

    def update(self, instance, validated_data):
        payment_plans_data = validated_data.pop('payment_plans', None)
        milestones_data = validated_data.pop('milestones', None)
        old_values = {}
        for field, value in validated_data.items():
            old_val = getattr(instance, field)
            if str(old_val) != str(value):
                old_values[field] = str(old_val)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        request = self.context.get('request')
        user = request.user if request else None
        for field, old_val in old_values.items():
            ContractChangeLog.objects.create(
                contract=instance,
                field_name=field,
                old_value=old_val,
                new_value=str(getattr(instance, field)),
                changed_by=user,
            )
        if payment_plans_data is not None:
            instance.payment_plans.all().delete()
            for plan_data in payment_plans_data:
                PaymentPlan.objects.create(contract=instance, **plan_data)
        if milestones_data is not None:
            instance.milestones.all().delete()
            for milestone_data in milestones_data:
                ContractMilestone.objects.create(contract=instance, **milestone_data)
        update_contract_metrics(instance)
        return instance


class ContractListSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    approval_status_display = serializers.CharField(source='get_approval_status_display', read_only=True)
    renewal_status_display = serializers.CharField(source='get_renewal_status_display', read_only=True)

    class Meta:
        model = Contract
        fields = [
            'id', 'contract_no', 'title', 'client_name', 'amount', 'base_amount', 'currency',
            'region', 'sign_date', 'status', 'status_display',
            'payment_status', 'payment_status_display',
            'approval_status', 'approval_status_display',
            'renewal_status', 'renewal_status_display',
            'quality_score', 'salesperson', 'department',
            'created_by_name', 'created_at',
        ]
