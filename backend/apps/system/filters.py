import django_filters
from .models import OperationLog


class OperationLogFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    action = django_filters.CharFilter(field_name='action', lookup_expr='exact')
    category = django_filters.CharFilter(field_name='category', lookup_expr='exact')
    level = django_filters.CharFilter(field_name='level', lookup_expr='exact')
    method = django_filters.CharFilter(field_name='method', lookup_expr='exact')
    module = django_filters.CharFilter(field_name='module', lookup_expr='exact')
    status_code = django_filters.NumberFilter(field_name='status_code', lookup_expr='exact')
    username = django_filters.CharFilter(field_name='user__username', lookup_expr='icontains')
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = OperationLog
        fields = ['action', 'category', 'level', 'method', 'module', 'status_code', 'username', 'start_date', 'end_date']

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        from django.db.models import Q
        return queryset.filter(
            Q(user__username__icontains=value)
            | Q(action__icontains=value)
            | Q(target__icontains=value)
            | Q(detail__icontains=value)
            | Q(ip_address__icontains=value)
            | Q(path__icontains=value)
        )
