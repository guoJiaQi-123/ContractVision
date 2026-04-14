import django_filters

from .models import Contract


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

    class Meta:
        model = Contract
        fields = [
            'contract_no', 'title', 'client_name', 'status',
            'payment_status', 'delivery_status', 'region',
            'department', 'salesperson', 'product_type',
        ]
