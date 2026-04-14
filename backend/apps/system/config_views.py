from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.contracts.models import Contract, ContractMilestone, PaymentPlan
from apps.users.permissions import IsAdmin
from core.response import success_response

from .models import (
    AlertMessage,
    AlertRule,
    CurrencyRate,
    DashboardConfig,
    DataPermissionRule,
    DataTemplate,
    SalesTarget,
    StampTaxRule,
)
from .serializers import (
    AlertMessageSerializer,
    AlertRuleSerializer,
    CurrencyRateSerializer,
    DashboardConfigSerializer,
    DataPermissionRuleSerializer,
    DataTemplateSerializer,
    SalesTargetSerializer,
    StampTaxRuleSerializer,
)


class StandardizedAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdmin]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return success_response(data=self.get_serializer(serializer.instance).data, message='创建成功')

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return success_response(data=self.get_serializer(serializer.instance).data, message='更新成功')

    def destroy(self, request, *args, **kwargs):
        self.perform_destroy(self.get_object())
        return success_response(message='删除成功')


class DataPermissionRuleViewSet(StandardizedAdminViewSet):
    queryset = DataPermissionRule.objects.select_related('user').all()
    serializer_class = DataPermissionRuleSerializer


class AlertRuleViewSet(StandardizedAdminViewSet):
    queryset = AlertRule.objects.all()
    serializer_class = AlertRuleSerializer


class AlertMessageViewSet(StandardizedAdminViewSet):
    queryset = AlertMessage.objects.select_related('contract', 'rule', 'owner', 'processed_by').all()
    serializer_class = AlertMessageSerializer

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        alert = self.get_object()
        alert.status = AlertMessage.Status.PROCESSED
        alert.processed_by = request.user
        alert.processed_at = timezone.now()
        alert.save(update_fields=['status', 'processed_by', 'processed_at'])
        return success_response(data=AlertMessageSerializer(alert).data, message='预警已处理')

    @action(detail=False, methods=['post'])
    def scan(self, request):
        today = timezone.now().date()
        created_count = 0
        rules = AlertRule.objects.filter(is_active=True)

        def create_alert(rule, contract, title, content, due_date):
            nonlocal created_count
            exists = AlertMessage.objects.filter(
                contract=contract,
                rule=rule,
                title=title,
                status=AlertMessage.Status.PENDING,
            ).exists()
            if exists:
                return
            AlertMessage.objects.create(
                contract=contract,
                rule=rule,
                title=title,
                content=content,
                warning_type=rule.rule_type,
                level=rule.level,
                owner=contract.renewal_owner or contract.created_by,
                due_date=due_date,
            )
            created_count += 1

        for rule in rules:
            threshold_date = today + timedelta(days=rule.remind_days)
            if rule.rule_type == AlertRule.RuleType.PAYMENT:
                plans = PaymentPlan.objects.filter(paid_date__isnull=True, due_date__lte=threshold_date)
                for plan in plans:
                    create_alert(
                        rule,
                        plan.contract,
                        f'付款预警 - {plan.contract.contract_no}',
                        f'付款节点「{plan.phase}」将于 {plan.due_date} 到期',
                        plan.due_date,
                    )
            elif rule.rule_type == AlertRule.RuleType.DELIVERY:
                milestones = ContractMilestone.objects.filter(
                    node_type=ContractMilestone.NodeType.DELIVERY,
                    planned_date__lte=threshold_date,
                ).exclude(status=ContractMilestone.Status.COMPLETED)
                for milestone in milestones:
                    create_alert(
                        rule,
                        milestone.contract,
                        f'交付预警 - {milestone.contract.contract_no}',
                        f'交付节点「{milestone.name}」计划于 {milestone.planned_date} 完成',
                        milestone.planned_date,
                    )
            elif rule.rule_type == AlertRule.RuleType.CONTRACT:
                contracts = Contract.objects.filter(end_date__isnull=False, end_date__lte=threshold_date).exclude(
                    renewal_status=Contract.RenewalStatus.RENEWED
                )
                for contract in contracts:
                    create_alert(
                        rule,
                        contract,
                        f'到期预警 - {contract.contract_no}',
                        f'合同将于 {contract.end_date} 到期，请及时跟进续签',
                        contract.end_date,
                    )
            elif rule.rule_type == AlertRule.RuleType.INVOICE:
                plans = PaymentPlan.objects.filter(
                    invoice_status=PaymentPlan.InvoiceStatus.PENDING,
                    due_date__lte=threshold_date,
                )
                for plan in plans:
                    create_alert(
                        rule,
                        plan.contract,
                        f'发票预警 - {plan.contract.contract_no}',
                        f'付款节点「{plan.phase}」尚未开票',
                        plan.due_date,
                    )
            elif rule.rule_type == AlertRule.RuleType.TARGET:
                for target in SalesTarget.objects.all():
                    actual_amount = Decimal('0')
                    contracts = Contract.objects.filter(sign_date__gte=target.start_date, sign_date__lte=target.end_date)
                    if target.target_type == SalesTarget.TargetType.SALESPERSON:
                        contracts = contracts.filter(salesperson=target.owner_value)
                    elif target.target_type == SalesTarget.TargetType.DEPARTMENT:
                        contracts = contracts.filter(department=target.owner_value)
                    elif target.target_type == SalesTarget.TargetType.REGION:
                        contracts = contracts.filter(region=target.owner_value)
                    actual_amount = contracts.aggregate(total=Sum('base_amount'))['total'] or Decimal('0')
                    progress = float(actual_amount / target.target_amount * 100) if target.target_amount else 0
                    if progress < float(target.warning_threshold):
                        AlertMessage.objects.get_or_create(
                            contract=None,
                            rule=rule,
                            title=f'目标预警 - {target.name}',
                            defaults={
                                'content': f'{target.owner_value} 当前达成率 {progress:.2f}%，低于阈值 {target.warning_threshold}%',
                                'warning_type': rule.rule_type,
                                'level': rule.level,
                                'due_date': target.end_date,
                            },
                        )
                        created_count += 1

        return success_response(data={'created_count': created_count}, message='预警扫描完成')


class SalesTargetViewSet(StandardizedAdminViewSet):
    queryset = SalesTarget.objects.all()
    serializer_class = SalesTargetSerializer


class DashboardConfigViewSet(StandardizedAdminViewSet):
    queryset = DashboardConfig.objects.select_related('created_by').all()
    serializer_class = DashboardConfigSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DataTemplateViewSet(StandardizedAdminViewSet):
    queryset = DataTemplate.objects.all()
    serializer_class = DataTemplateSerializer


class CurrencyRateViewSet(StandardizedAdminViewSet):
    queryset = CurrencyRate.objects.all()
    serializer_class = CurrencyRateSerializer


class StampTaxRuleViewSet(StandardizedAdminViewSet):
    queryset = StampTaxRule.objects.all()
    serializer_class = StampTaxRuleSerializer


class MobileDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        config = DashboardConfig.objects.filter(is_mobile=True, is_active=True).order_by('-updated_at').first()
        contracts = Contract.objects.all()
        data = {
            'config': DashboardConfigSerializer(config).data if config else None,
            'summary': {
                'total_contracts': contracts.count(),
                'total_amount': str(contracts.aggregate(total=Sum('base_amount'))['total'] or 0),
                'pending_alerts': AlertMessage.objects.filter(status=AlertMessage.Status.PENDING).count(),
                'expiring_contracts': contracts.filter(
                    end_date__isnull=False,
                    end_date__lte=timezone.now().date() + timedelta(days=30)
                ).count(),
            },
        }
        return success_response(data=data)
