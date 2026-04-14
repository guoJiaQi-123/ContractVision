import datetime
from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.contracts.models import Contract, PaymentPlan
from core.response import success_response


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total_stats = Contract.objects.aggregate(
            total_contracts=Count('id'),
            total_amount=Sum('amount'),
        )

        active_count = Contract.objects.filter(status='active').count()
        completed_count = Contract.objects.filter(status='completed').count()

        month_stats = Contract.objects.filter(created_at__gte=month_start).aggregate(
            this_month_new=Count('id'),
            this_month_amount=Sum('amount'),
        )

        data = {
            'total_contracts': total_stats['total_contracts'] or 0,
            'total_amount': str(total_stats['total_amount'] or 0),
            'active_contracts': active_count,
            'completed_contracts': completed_count,
            'this_month_new': month_stats['this_month_new'] or 0,
            'this_month_amount': str(month_stats['this_month_amount'] or 0),
        }
        return success_response(data=data)


class ContractTrendView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        contracts = (
            Contract.objects
            .filter(created_at__date__gte=start_date)
            .extra(select={'date': 'DATE(created_at)'})
            .values('date')
            .annotate(count=Count('id'), amount=Sum('amount'))
            .order_by('date')
        )

        data = [
            {
                'date': str(item['date']),
                'count': item['count'],
                'amount': str(item['amount'] or 0),
            }
            for item in contracts
        ]
        return success_response(data=data)


class RegionDistributionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        distribution = (
            Contract.objects
            .exclude(region='')
            .values('region')
            .annotate(count=Count('id'), amount=Sum('amount'))
            .order_by('-amount')
        )

        data = [
            {
                'region': item['region'],
                'count': item['count'],
                'amount': str(item['amount'] or 0),
            }
            for item in distribution
        ]
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
        data = [
            {
                'status': status_map.get(item['status'], item['status']),
                'key': item['status'],
                'count': item['count'],
            }
            for item in distribution
        ]
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
