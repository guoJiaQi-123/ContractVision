import django_filters
from django.db.models import Q
from django.utils import timezone

from .models import Contract, PaymentPlan


class ContractFilter(django_filters.FilterSet):
    contract_no = django_filters.CharFilter(lookup_expr='icontains')
    title = django_filters.CharFilter(lookup_expr='icontains')
    client_name = django_filters.CharFilter(lookup_expr='icontains')
    status = django_filters.ChoiceFilter(choices=Contract.Status.choices)
    payment_status = django_filters.ChoiceFilter(choices=Contract.PaymentStatus.choices)
    delivery_status = django_filters.ChoiceFilter(choices=Contract.DeliveryStatus.choices)
    region = django_filters.CharFilter(lookup_expr='icontains')
    department = django_filters.CharFilter(lookup_expr='icontains')
    salesperson = django_filters.CharFilter(lookup_expr='icontains')
    product_type = django_filters.CharFilter(lookup_expr='icontains')
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    sign_date_from = django_filters.DateFilter(field_name='sign_date', lookup_expr='gte')
    sign_date_to = django_filters.DateFilter(field_name='sign_date', lookup_expr='lte')
    created_at_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    has_overdue = django_filters.BooleanFilter(method='filter_has_overdue', label='存在逾期付款')

    class Meta:
        model = Contract
        fields = [
            'contract_no', 'title', 'client_name', 'status',
            'payment_status', 'delivery_status', 'region',
            'department', 'salesperson', 'product_type',
        ]

    def filter_has_overdue(self, queryset, name, value):
        if value:
            today = timezone.now().date()
            overdue_contract_ids = PaymentPlan.objects.filter(
                Q(status__in=[PaymentPlan.Status.OVERDUE, PaymentPlan.Status.SEVERE_OVERDUE])
                | Q(status=PaymentPlan.Status.PENDING, due_date__lt=today)
            ).values_list('contract_id', flat=True)
            return queryset.filter(id__in=overdue_contract_ids)
        return queryset
