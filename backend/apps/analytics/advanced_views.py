from decimal import Decimal

from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.contracts.models import Contract
from apps.contracts.serializers import ContractListSerializer
from apps.contracts.services import apply_data_permission
from apps.system.models import AlertMessage, DashboardConfig, SalesTarget
from apps.users.permissions import IsAdmin
from core.response import success_response


class SalesTargetProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        targets = SalesTarget.objects.all().order_by('-start_date')
        result = []
        warning_list = []
        for target in targets:
            contracts = Contract.objects.filter(sign_date__gte=target.start_date, sign_date__lte=target.end_date)
            contracts = apply_data_permission(contracts, request.user)
            if target.target_type == SalesTarget.TargetType.SALESPERSON:
                contracts = contracts.filter(salesperson=target.owner_value)
            elif target.target_type == SalesTarget.TargetType.DEPARTMENT:
                contracts = contracts.filter(department=target.owner_value)
            elif target.target_type == SalesTarget.TargetType.REGION:
                contracts = contracts.filter(region=target.owner_value)

            actual_amount = contracts.aggregate(total=Sum('base_amount'))['total'] or Decimal('0')
            progress = float(actual_amount / target.target_amount * 100) if target.target_amount else 0
            item = {
                'id': target.id,
                'name': target.name,
                'target_type': target.target_type,
                'owner_value': target.owner_value,
                'period_label': target.period_label,
                'target_amount': str(target.target_amount),
                'actual_amount': str(actual_amount),
                'progress_rate': round(progress, 2),
                'warning_threshold': float(target.warning_threshold),
                'remaining_amount': str(max(target.target_amount - actual_amount, Decimal('0'))),
            }
            result.append(item)
            if progress < float(target.warning_threshold):
                warning_list.append(item)
        return success_response(data={'list': result, 'warnings': warning_list})


class DashboardDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        dashboard_id = request.query_params.get('dashboard_id')
        config = DashboardConfig.objects.filter(pk=dashboard_id).first() if dashboard_id else None
        if not config:
            config = DashboardConfig.objects.filter(is_active=True, is_mobile=False).order_by('-updated_at').first()

        queryset = apply_data_permission(Contract.objects.all(), request.user)
        widgets = config.widgets if config else []
        widget_data = []
        for widget in widgets:
            widget_type = widget.get('type')
            dimension = widget.get('dimension', 'month')
            if widget_type == 'metric':
                metric = widget.get('metric', 'amount')
                value = queryset.aggregate(
                    total_amount=Sum('base_amount'),
                    total_contracts=Count('id'),
                )
                widget_data.append({
                    'id': widget.get('id'),
                    'type': widget_type,
                    'title': widget.get('title'),
                    'value': str(value['total_amount'] or 0) if metric == 'amount' else value['total_contracts'],
                })
            elif widget_type == 'trend':
                trends = (
                    queryset.annotate(month=TruncMonth('sign_date'))
                    .values('month')
                    .annotate(amount=Sum('base_amount'))
                    .order_by('month')
                )
                widget_data.append({
                    'id': widget.get('id'),
                    'type': widget_type,
                    'title': widget.get('title'),
                    'dimension': dimension,
                    'labels': [item['month'].strftime('%Y-%m') for item in trends if item['month']],
                    'series': [str(item['amount'] or 0) for item in trends],
                })
            elif widget_type == 'ranking':
                field = widget.get('field', 'salesperson')
                ranking = queryset.exclude(**{field: ''}).values(field).annotate(amount=Sum('base_amount')).order_by('-amount')[:10]
                widget_data.append({
                    'id': widget.get('id'),
                    'type': widget_type,
                    'title': widget.get('title'),
                    'field': field,
                    'list': [{field: item[field], 'amount': str(item['amount'] or 0)} for item in ranking],
                })

        return success_response(data={
            'config': {
                'id': config.id if config else None,
                'name': config.name if config else '默认驾驶舱',
                'layout': config.layout if config else [],
                'widgets': widgets,
            },
            'widget_data': widget_data,
        })


class DrilldownAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    DIMENSION_MAP = {
        'region': 'region',
        'department': 'department',
        'salesperson': 'salesperson',
        'client': 'client_name',
        'product': 'product_type',
    }

    def get(self, request):
        dimension = request.query_params.get('dimension', 'region')
        field = self.DIMENSION_MAP.get(dimension, 'region')
        queryset = apply_data_permission(Contract.objects.all(), request.user)

        for filter_key, model_field in self.DIMENSION_MAP.items():
            value = request.query_params.get(filter_key)
            if value:
                queryset = queryset.filter(**{model_field: value})

        grouped = queryset.exclude(**{field: ''}).values(field).annotate(
            contract_count=Count('id'),
            total_amount=Sum('base_amount'),
            avg_amount=Avg('base_amount'),
        ).order_by('-total_amount')

        return success_response(data={
            'dimension': dimension,
            'list': [
                {
                    'name': item[field],
                    'contract_count': item['contract_count'],
                    'total_amount': str(item['total_amount'] or 0),
                    'avg_amount': str(item['avg_amount'] or 0),
                }
                for item in grouped
            ],
            'details': ContractListSerializer(queryset[:50], many=True).data,
        })


class TeamPerformanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        dimension = request.query_params.get('dimension', 'salesperson')
        field = 'department' if dimension == 'department' else 'salesperson'
        queryset = apply_data_permission(Contract.objects.all(), request.user)
        ranking = queryset.exclude(**{field: ''}).values(field).annotate(
            contract_count=Count('id'),
            total_amount=Sum('base_amount'),
            avg_amount=Avg('base_amount'),
            paid_amount=Sum('payment_plans__actual_amount'),
        ).order_by('-total_amount')

        data = []
        for item in ranking:
            owner_value = item[field]
            targets = SalesTarget.objects.filter(target_type=dimension, owner_value=owner_value)
            target_total = sum(Decimal(target.target_amount) for target in targets)
            actual_amount = Decimal(item['total_amount'] or 0)
            target_rate = float(actual_amount / target_total * 100) if target_total else 0
            paid_amount = Decimal(item['paid_amount'] or 0)
            data.append({
                field: owner_value,
                'contract_count': item['contract_count'],
                'total_amount': str(actual_amount),
                'avg_amount': str(item['avg_amount'] or 0),
                'recovery_rate': round(float(paid_amount / actual_amount * 100), 2) if actual_amount else 0,
                'target_amount': str(target_total),
                'target_rate': round(target_rate, 2),
            })
        return success_response(data=data)


class TaxAnalysisView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        queryset = Contract.objects.exclude(stamp_tax_amount=0)
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(sign_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(sign_date__lte=end_date)

        monthly = (
            queryset.annotate(month=TruncMonth('sign_date'))
            .values('month')
            .annotate(total_tax=Sum('stamp_tax_amount'), contract_count=Count('id'))
            .order_by('month')
        )
        by_type = queryset.values('contract_type').annotate(total_tax=Sum('stamp_tax_amount')).order_by('-total_tax')
        return success_response(data={
            'summary': {
                'total_tax': str(queryset.aggregate(total=Sum('stamp_tax_amount'))['total'] or 0),
                'contract_count': queryset.count(),
                'pending_alerts': AlertMessage.objects.filter(status=AlertMessage.Status.PENDING).count(),
            },
            'monthly': [
                {
                    'month': item['month'].strftime('%Y-%m') if item['month'] else '',
                    'total_tax': str(item['total_tax'] or 0),
                    'contract_count': item['contract_count'],
                }
                for item in monthly
            ],
            'contract_types': [
                {
                    'contract_type': item['contract_type'] or '未分类',
                    'total_tax': str(item['total_tax'] or 0),
                }
                for item in by_type
            ],
        })
