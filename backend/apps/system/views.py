from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated

from apps.users.permissions import IsAdmin
from core.response import success_response
from utils.export import export_to_excel

from .models import OperationLog
from .serializers import OperationLogSerializer


class OperationLogViewSet(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = OperationLog.objects.select_related('user').all()
    serializer_class = OperationLogSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    search_fields = ['user__username', 'action', 'target', 'ip_address']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)

    @action(detail=False, methods=['get'])
    def export(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset[:1000], many=True)
        columns = [
            {'key': 'username', 'label': '操作人', 'width': 15},
            {'key': 'action', 'label': '操作类型', 'width': 12},
            {'key': 'target', 'label': '操作对象', 'width': 30},
            {'key': 'ip_address', 'label': 'IP地址', 'width': 18},
            {'key': 'method', 'label': '请求方法', 'width': 10},
            {'key': 'status_code', 'label': '状态码', 'width': 10},
            {'key': 'created_at', 'label': '操作时间', 'width': 20},
        ]
        return export_to_excel(serializer.data, columns, filename='operation_logs.xlsx')
