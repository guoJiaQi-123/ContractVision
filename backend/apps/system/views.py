import csv

from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated

from apps.users.permissions import IsAdmin
from core.response import success_response
from utils.export import export_to_excel

from .models import Customer, Department, OperationLog, ProductType
from .serializers import (
    CustomerSerializer,
    DepartmentSerializer,
    DepartmentTreeSerializer,
    OperationLogSerializer,
    ProductTypeSerializer,
)
from .filters import OperationLogFilter


class OperationLogViewSet(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = OperationLog.objects.select_related("user").all()
    serializer_class = OperationLogSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_class = OperationLogFilter
    search_fields = [
        "user__username",
        "action",
        "target",
        "ip_address",
        "detail",
        "path",
    ]
    ordering_fields = ["created_at", "duration_ms"]
    ordering = ["-created_at"]

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

    @action(detail=False, methods=["get"])
    def summary(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        today = timezone.now().date()
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        total = queryset.count()
        today_count = queryset.filter(created_at__gte=today_start).count()

        category_counts = dict(
            queryset.values("category")
            .annotate(count=Count("id"))
            .values_list("category", "count")
        )
        level_counts = dict(
            queryset.values("level")
            .annotate(count=Count("id"))
            .values_list("level", "count")
        )
        action_counts = dict(
            queryset.values("action")
            .annotate(count=Count("id"))
            .values_list("action", "count")
        )
        module_counts = dict(
            queryset.values("module")
            .annotate(count=Count("id"))
            .values_list("module", "count")
        )

        error_count = queryset.filter(
            level__in=[OperationLog.Level.ERROR, OperationLog.Level.CRITICAL]
        ).count()

        recent_errors = queryset.filter(
            level__in=[OperationLog.Level.ERROR, OperationLog.Level.CRITICAL]
        ).order_by("-created_at")[:5]
        recent_errors_data = OperationLogSerializer(recent_errors, many=True).data

        data = {
            "total": total,
            "today_count": today_count,
            "error_count": error_count,
            "category_counts": category_counts,
            "level_counts": level_counts,
            "action_counts": action_counts,
            "module_counts": module_counts,
            "recent_errors": recent_errors_data,
        }
        return success_response(data=data)

    @action(detail=False, methods=["get"])
    def export(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        export_format = request.query_params.get("format", "xlsx")

        limit = min(int(request.query_params.get("limit", 5000)), 10000)
        logs = queryset[:limit]
        serializer = self.get_serializer(logs, many=True)

        if export_format == "csv":
            response = HttpResponse(content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = (
                'attachment; filename="operation_logs.csv"'
            )
            response.write("\ufeff")
            writer = csv.writer(response)
            writer.writerow(
                [
                    "ID",
                    "操作人",
                    "操作类型",
                    "日志分类",
                    "日志级别",
                    "操作对象",
                    "操作详情",
                    "IP地址",
                    "请求方法",
                    "请求路径",
                    "状态码",
                    "耗时(ms)",
                    "功能模块",
                    "操作时间",
                ]
            )
            for row in serializer.data:
                writer.writerow(
                    [
                        row.get("id"),
                        row.get("username", ""),
                        row.get("action", ""),
                        row.get("category_display", ""),
                        row.get("level_display", ""),
                        row.get("target", ""),
                        row.get("detail", ""),
                        row.get("ip_address", ""),
                        row.get("method", ""),
                        row.get("path", ""),
                        row.get("status_code", ""),
                        row.get("duration_ms", ""),
                        row.get("module", ""),
                        row.get("created_at", ""),
                    ]
                )
            return response

        columns = [
            {"key": "username", "label": "操作人", "width": 15},
            {"key": "action", "label": "操作类型", "width": 12},
            {"key": "category_display", "label": "日志分类", "width": 12},
            {"key": "level_display", "label": "日志级别", "width": 12},
            {"key": "target", "label": "操作对象", "width": 30},
            {"key": "detail", "label": "操作详情", "width": 30},
            {"key": "ip_address", "label": "IP地址", "width": 18},
            {"key": "method", "label": "请求方法", "width": 10},
            {"key": "status_code", "label": "状态码", "width": 10},
            {"key": "duration_ms", "label": "耗时(ms)", "width": 10},
            {"key": "module", "label": "功能模块", "width": 12},
            {"key": "created_at", "label": "操作时间", "width": 20},
        ]
        return export_to_excel(serializer.data, columns, filename="operation_logs.xlsx")

    @action(detail=False, methods=["get"])
    def filter_options(self, request):
        queryset = self.get_queryset()
        actions = list(
            queryset.values_list("action", flat=True).distinct().order_by("action")
        )
        modules = list(
            queryset.values_list("module", flat=True).distinct().order_by("module")
        )

        data = {
            "categories": [
                {"value": c[0], "label": c[1]} for c in OperationLog.Category.choices
            ],
            "levels": [
                {"value": l[0], "label": l[1]} for l in OperationLog.Level.choices
            ],
            "actions": actions,
            "modules": modules,
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE"],
        }
        return success_response(data=data)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    search_fields = ["name", "code"]
    ordering_fields = ["sort_order", "created_at"]
    ordering = ["sort_order", "id"]

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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="部门创建成功")

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="部门更新成功")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message="部门已删除")

    @action(detail=False, methods=["get"])
    def generate_code(self, request):
        import datetime

        today = datetime.date.today()
        prefix = f"DP{today.strftime('%Y%m%d')}"
        last = (
            Department.objects.filter(code__startswith=prefix).order_by("-code").first()
        )
        seq = 1
        if last:
            try:
                seq = int(last.code[-4:]) + 1
            except ValueError:
                seq = 1
        return success_response(data={"code": f"{prefix}{seq:04d}"})

    @action(detail=False, methods=["get"])
    def options(self, request):
        queryset = (
            Department.objects.filter(is_active=True)
            .values("id", "name", "code")
            .order_by("sort_order")
        )
        return success_response(data=list(queryset))

    @action(detail=False, methods=["get"])
    def tree(self, request):
        root_departments = Department.objects.filter(parent__isnull=True).order_by(
            "sort_order", "id"
        )
        serializer = DepartmentTreeSerializer(root_departments, many=True)
        return success_response(data=serializer.data)

    @action(detail=False, methods=["get"])
    def admin_users(self, request):
        from apps.users.models import User

        users = (
            User.objects.filter(
                role__in=[User.Role.ADMIN, User.Role.OPERATOR],
                is_active=True,
            )
            .values("id", "username", "role")
            .order_by("username")
        )
        return success_response(data=list(users))


class ProductTypeViewSet(viewsets.ModelViewSet):
    queryset = ProductType.objects.all()
    serializer_class = ProductTypeSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    search_fields = ["name", "code", "category"]
    ordering_fields = ["sort_order", "created_at"]
    ordering = ["sort_order", "id"]

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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="产品类型创建成功")

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="产品类型更新成功")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message="产品类型已删除")

    @action(detail=False, methods=["get"])
    def generate_code(self, request):
        import datetime

        today = datetime.date.today()
        prefix = f"PT{today.strftime('%Y%m%d')}"
        last = (
            ProductType.objects.filter(code__startswith=prefix)
            .order_by("-code")
            .first()
        )
        seq = 1
        if last:
            try:
                seq = int(last.code[-4:]) + 1
            except ValueError:
                seq = 1
        return success_response(data={"code": f"{prefix}{seq:04d}"})

    @action(detail=False, methods=["get"])
    def options(self, request):
        queryset = (
            ProductType.objects.filter(is_active=True)
            .values("id", "name", "code", "category")
            .order_by("sort_order")
        )
        return success_response(data=list(queryset))


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "code", "short_name", "contact_person"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsAdmin()]
        return super().get_permissions()

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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="客户创建成功")

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="客户更新成功")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message="客户已删除")

    @action(detail=False, methods=["get"])
    def generate_code(self, request):
        import datetime

        today = datetime.date.today()
        prefix = f"KH{today.strftime('%Y%m%d')}"
        last = (
            Customer.objects.filter(code__startswith=prefix).order_by("-code").first()
        )
        seq = 1
        if last:
            try:
                seq = int(last.code[-4:]) + 1
            except ValueError:
                seq = 1
        return success_response(data={"code": f"{prefix}{seq:04d}"})

    @action(detail=False, methods=["get"])
    def options(self, request):
        queryset = (
            Customer.objects.filter(is_active=True)
            .values("id", "name", "code", "short_name", "contact_person")
            .order_by("name")
        )
        return success_response(data=list(queryset))
