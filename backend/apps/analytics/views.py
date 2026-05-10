import datetime
from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.contracts.models import Contract, PaymentPlan
from apps.system.models import SalesTarget
from core.response import success_response


def _month_offset(base, months_back):
    y = base.year
    m = base.month - months_back
    while m <= 0:
        m += 12
        y -= 1
    return base.replace(year=y, month=m, day=1)


def _determine_granularity(start_date, end_date):
    delta = (end_date - start_date).days
    if delta <= 90:
        return 'day', TruncDay, '%Y-%m-%d'
    elif delta <= 365:
        return 'week', TruncWeek, '%Y-W%W'
    else:
        return 'month', TruncMonth, '%Y-%m'


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total_stats = Contract.objects.aggregate(
            total_contracts=Count('id'),
            total_amount=Sum('amount'),
        )

        month_stats = Contract.objects.filter(created_at__gte=month_start).aggregate(
            this_month_new=Count('id'),
        )

        overdue_count = PaymentPlan.objects.filter(
            status__in=[PaymentPlan.Status.PENDING, PaymentPlan.Status.OVERDUE, PaymentPlan.Status.SEVERE_OVERDUE],
            due_date__lt=datetime.date.today()
        ).values('contract').distinct().count()

        data = {
            'totalContracts': total_stats['total_contracts'] or 0,
            'totalAmount': float(total_stats['total_amount'] or 0),
            'monthlyNew': month_stats['this_month_new'] or 0,
            'pendingAlerts': overdue_count,
        }
        return success_response(data=data)


class ContractTrendView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        start_str = request.query_params.get('start_date')
        end_str = request.query_params.get('end_date')
        force_monthly = request.query_params.get('granularity') == 'month'

        if start_str and end_str:
            try:
                start_date = datetime.datetime.strptime(start_str, '%Y-%m-%d').date()
                end_date = datetime.datetime.strptime(end_str, '%Y-%m-%d').date()
            except ValueError:
                start_date = (now - timedelta(days=180)).date()
                end_date = now.date()
        else:
            months = int(request.query_params.get('months', 6))
            start_date = _month_offset(now, months - 1).date()
            end_date = now.date()
            force_monthly = True

        if force_monthly:
            granularity, trunc_cls, fmt = 'month', TruncMonth, '%Y-%m'
        else:
            granularity, trunc_cls, fmt = _determine_granularity(start_date, end_date)

        trends = (
            Contract.objects
            .filter(sign_date__gte=start_date, sign_date__lte=end_date)
            .annotate(period=trunc_cls('sign_date'))
            .values('period')
            .annotate(amount=Sum('amount'))
            .order_by('period')
        )

        trend_map = {}
        for item in trends:
            if item['period']:
                trend_map[item['period'].strftime(fmt)] = float(item['amount'] or 0)

        if granularity == 'day':
            labels = []
            current = start_date
            while current <= end_date:
                labels.append(current.strftime(fmt))
                current += timedelta(days=1)
        elif granularity == 'week':
            labels = []
            current = start_date
            while current <= end_date:
                labels.append(current.strftime(fmt))
                current += timedelta(weeks=1)
        else:
            labels = []
            current = start_date.replace(day=1)
            end_month = end_date.replace(day=1)
            while current <= end_month:
                labels.append(current.strftime(fmt))
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)

        revenue = [trend_map.get(label, 0) for label in labels]

        target = []
        for label in labels:
            if granularity == 'month':
                sales_target = SalesTarget.objects.filter(period_label=label).first()
                target.append(float(sales_target.target_amount) if sales_target else 0)
            else:
                target.append(0)

        data = {
            'labels': labels,
            'revenue': revenue,
            'target': target,
            'granularity': granularity,
        }
        return success_response(data=data)


class RegionDistributionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        distribution = (
            Contract.objects
            .exclude(region='')
            .values('region')
            .annotate(amount=Sum('amount'))
            .order_by('-amount')
        )

        data = {
            'regions': [item['region'] for item in distribution],
            'counts': [float(item['amount'] or 0) for item in distribution],
        }
        return success_response(data=data)


class StatusDistributionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        distribution = (
            Contract.objects
            .values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        status_map = dict(Contract.Status.choices)
        items = [
            {
                'name': status_map.get(item['status'], item['status']),
                'value': item['count'],
            }
            for item in distribution
        ]
        data = {'items': items}
        return success_response(data=data)


class TopClientsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        clients = (
            Contract.objects
            .values('client_name')
            .annotate(count=Count('id'), total_amount=Sum('amount'))
            .order_by('-total_amount')[:limit]
        )

        data = [
            {
                'client_name': item['client_name'],
                'count': item['count'],
                'total_amount': str(item['total_amount'] or 0),
            }
            for item in clients
        ]
        return success_response(data=data)


class SalespersonRankingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        ranking = (
            Contract.objects
            .exclude(salesperson='')
            .values('salesperson')
            .annotate(count=Count('id'), total_amount=Sum('amount'))
            .order_by('-total_amount')[:limit]
        )

        data = [
            {
                'salesperson': item['salesperson'],
                'count': item['count'],
                'total_amount': str(item['total_amount'] or 0),
            }
            for item in ranking
        ]
        return success_response(data=data)


class ProductDistributionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        distribution = (
            Contract.objects
            .exclude(product_type='')
            .values('product_type')
            .annotate(count=Count('id'), amount=Sum('amount'))
            .order_by('-amount')
        )
        data = [
            {
                'product_type': item['product_type'],
                'count': item['count'],
                'amount': str(item['amount'] or 0),
            }
            for item in distribution
        ]
        return success_response(data=data)


class MonthlyTrendView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        months = int(request.query_params.get('months', 12))
        now = timezone.now()

        start_date = now - timedelta(days=months * 30)
        trends = (
            Contract.objects
            .filter(created_at__gte=start_date)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'), amount=Sum('amount'))
            .order_by('month')
        )
        data = {
            'months': [item['month'].strftime('%Y-%m') for item in trends],
            'counts': [item['count'] for item in trends],
            'amounts': [str(item['amount'] or 0) for item in trends],
        }
        return success_response(data=data)


class DepartmentRankingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        ranking = (
            Contract.objects
            .exclude(department='')
            .values('department')
            .annotate(count=Count('id'), total_amount=Sum('amount'))
            .order_by('-total_amount')[:limit]
        )
        data = [
            {
                'department': item['department'],
                'count': item['count'],
                'total_amount': str(item['total_amount'] or 0),
            }
            for item in ranking
        ]
        return success_response(data=data)


class OverviewSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)

        total = Contract.objects.aggregate(
            total_contracts=Count('id'),
            total_amount=Sum('amount'),
        )

        this_month = Contract.objects.filter(created_at__gte=month_start).aggregate(
            new_contracts=Count('id'),
            new_amount=Sum('amount'),
        )

        last_month = Contract.objects.filter(
            created_at__gte=last_month_start,
            created_at__lt=month_start
        ).aggregate(
            new_contracts=Count('id'),
            new_amount=Sum('amount'),
        )

        active = Contract.objects.filter(status='active').count()
        completed = Contract.objects.filter(status='completed').count()

        overdue_count = PaymentPlan.objects.filter(
            status='pending',
            due_date__lt=datetime.date.today()
        ).values('contract').distinct().count()

        data = {
            'total_contracts': total['total_contracts'] or 0,
            'total_amount': str(total['total_amount'] or 0),
            'active_contracts': active,
            'completed_contracts': completed,
            'this_month_new': this_month['new_contracts'] or 0,
            'this_month_amount': str(this_month['new_amount'] or 0),
            'last_month_new': last_month['new_contracts'] or 0,
            'last_month_amount': str(last_month['new_amount'] or 0),
            'overdue_contracts': overdue_count,
        }
        return success_response(data=data)
