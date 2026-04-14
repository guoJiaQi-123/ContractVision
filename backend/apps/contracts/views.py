from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.users.permissions import IsOperator
from core.response import error_response, success_response
from utils.export import export_to_excel, export_to_pdf

from .filters import ContractFilter
from .models import ApprovalProcess, ApprovalRequest, Contract
from .serializers import ContractCreateSerializer, ContractListSerializer, ContractSerializer
from .services import apply_data_permission, compute_contract_progress, update_contract_metrics


class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.select_related('created_by', 'renewal_owner').prefetch_related(
        'payment_plans',
        'milestones',
        'change_logs',
        'change_requests',
    ).all()
    permission_classes = [IsAuthenticated]
    filterset_class = ContractFilter
    search_fields = ['contract_no', 'title', 'client_name', 'salesperson']
    ordering_fields = ['amount', 'sign_date', 'created_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        return apply_data_permission(queryset, self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return ContractListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ContractCreateSerializer
        return ContractSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsOperator()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def _get_approval_process(self, action_type, amount=None):
        queryset = ApprovalProcess.objects.filter(action_type=action_type, is_active=True).order_by('-min_amount')
        if amount is None:
            return queryset.first()
        for process in queryset:
            if amount >= process.min_amount:
                return process
        return None

    def _create_approval_request(self, contract, process, action_type, payload, title):
        ApprovalRequest.objects.create(
            contract=contract,
            process=process,
            action_type=action_type,
            title=title,
            request_payload=payload,
            requested_by=self.request.user,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            self.perform_create(serializer)
            contract = serializer.instance
            update_contract_metrics(contract)
            process = self._get_approval_process(ApprovalProcess.ActionType.CREATE, contract.base_amount)
            if process:
                contract.approval_status = Contract.ApprovalStatus.PENDING
                contract.save(update_fields=['approval_status', 'updated_at'])
                self._create_approval_request(
                    contract=contract,
                    process=process,
                    action_type=ApprovalProcess.ActionType.CREATE,
                    payload=ContractSerializer(contract).data,
                    title=f'合同新增审批 - {contract.contract_no}',
                )
        return success_response(
            data=ContractSerializer(serializer.instance).data,
            message='合同已创建并提交审批' if serializer.instance.approval_status == Contract.ApprovalStatus.PENDING else '合同创建成功',
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status in (Contract.Status.TERMINATED, Contract.Status.VOIDED):
            return error_response(message='已终止或作废的合同不允许编辑')
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        amount = request.data.get('base_amount') or request.data.get('amount') or instance.base_amount or instance.amount
        process = self._get_approval_process(ApprovalProcess.ActionType.UPDATE, amount)
        if process:
            instance.approval_status = Contract.ApprovalStatus.PENDING
            instance.save(update_fields=['approval_status', 'updated_at'])
            self._create_approval_request(
                contract=instance,
                process=process,
                action_type=ApprovalProcess.ActionType.UPDATE,
                payload=request.data,
                title=f'合同修改审批 - {instance.contract_no}',
            )
            return success_response(
                data=ContractSerializer(instance).data,
                message='变更已提交审批，通过后生效',
            )
        serializer.save()
        update_contract_metrics(instance)
        return success_response(
            data=ContractSerializer(instance).data,
            message='合同更新成功',
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        process = self._get_approval_process(ApprovalProcess.ActionType.DELETE, instance.base_amount or instance.amount)
        if process:
            instance.approval_status = Contract.ApprovalStatus.PENDING
            instance.save(update_fields=['approval_status', 'updated_at'])
            self._create_approval_request(
                contract=instance,
                process=process,
                action_type=ApprovalProcess.ActionType.DELETE,
                payload={'id': instance.id, 'contract_no': instance.contract_no},
                title=f'合同删除审批 - {instance.contract_no}',
            )
            return success_response(message='删除申请已提交审批')
        instance.delete()
        return success_response(message='合同已删除')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        update_contract_metrics(instance)
        serializer = ContractSerializer(instance)
        return success_response(data=serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    @action(detail=True, methods=['get'])
    def fulfillment(self, request, pk=None):
        contract = self.get_object()
        return success_response(data=compute_contract_progress(contract))

    @action(detail=False, methods=['get'])
    def renewal_summary(self, request):
        today = timezone.now().date()
        within_days = int(request.query_params.get('days', 30))
        end_date = today + timedelta(days=within_days)
        queryset = self.filter_queryset(self.get_queryset()).filter(
            end_date__isnull=False,
            end_date__lte=end_date,
        ).order_by('end_date')
        serializer = ContractListSerializer(queryset[:200], many=True)
        data = {
            'summary': {
                'expiring_soon': queryset.filter(end_date__gte=today).count(),
                'expired': queryset.filter(end_date__lt=today).count(),
                'renewed': queryset.filter(renewal_status=Contract.RenewalStatus.RENEWED).count(),
                'not_renewed': queryset.filter(renewal_status=Contract.RenewalStatus.NOT_RENEWED).count(),
            },
            'list': serializer.data,
        }
        return success_response(data=data)

    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        contract = self.get_object()
        contract.renewal_status = Contract.RenewalStatus.RENEWED
        contract.renewal_contract_no = request.data.get('renewal_contract_no', '')
        contract.renewal_reminder_days = request.data.get('renewal_reminder_days', contract.renewal_reminder_days)
        renewal_owner_id = request.data.get('renewal_owner')
        if renewal_owner_id:
            contract.renewal_owner_id = renewal_owner_id
        contract.save(update_fields=[
            'renewal_status',
            'renewal_contract_no',
            'renewal_reminder_days',
            'renewal_owner',
            'updated_at',
        ])
        return success_response(data=ContractSerializer(contract).data, message='续签信息更新成功')

    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        contract = self.get_object()
        status_value = request.data.get('status')
        if status_value not in (Contract.Status.TERMINATED, Contract.Status.VOIDED):
            return error_response(message='仅支持终止或作废操作')
        contract.status = status_value
        contract.terminated_reason = request.data.get('reason', '')
        contract.terminated_at = request.data.get('effective_date') or timezone.now().date()
        contract.termination_attachments = request.data.get('attachments', [])
        contract.save(update_fields=[
            'status',
            'terminated_reason',
            'terminated_at',
            'termination_attachments',
            'updated_at',
        ])
        return success_response(data=ContractSerializer(contract).data, message='合同状态更新成功')

    @action(detail=True, methods=['post'])
    def recalculate_quality(self, request, pk=None):
        contract = self.get_object()
        update_contract_metrics(contract)
        return success_response(data=ContractSerializer(contract).data, message='合同质量评分已更新')

    @action(detail=False, methods=['get'])
    def export(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = ContractListSerializer(queryset, many=True)
        columns = [
            {'key': 'contract_no', 'label': '合同编号', 'width': 20},
            {'key': 'title', 'label': '合同标题', 'width': 30},
            {'key': 'client_name', 'label': '客户名称', 'width': 20},
            {'key': 'amount', 'label': '合同金额', 'width': 15},
            {'key': 'status_display', 'label': '状态', 'width': 12},
            {'key': 'payment_status_display', 'label': '付款状态', 'width': 12},
            {'key': 'salesperson', 'label': '销售人员', 'width': 15},
            {'key': 'sign_date', 'label': '签订日期', 'width': 15},
        ]
        return export_to_excel(serializer.data, columns, filename='contracts.xlsx')

    @action(detail=True, methods=['get'])
    def change_logs(self, request, pk=None):
        contract = self.get_object()
        from .serializers import ContractChangeLogSerializer
        logs = contract.change_logs.select_related('changed_by').all()
        serializer = ContractChangeLogSerializer(logs, many=True)
        return success_response(data=serializer.data)

    @action(detail=False, methods=['post'])
    def batch_import(self, request):
        file = request.FILES.get('file')
        if not file:
            return error_response(message='请上传文件')

        import pandas as pd
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return error_response(message='仅支持Excel或CSV格式文件')
        except Exception as e:
            return error_response(message=f'文件解析失败: {str(e)}')

        required_columns = ['contract_no', 'title', 'client_name', 'amount']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            return error_response(
                message='文件缺少必要列',
                data={'missing_columns': missing},
            )

        success_count = 0
        error_list = []
        for idx, row in df.iterrows():
            try:
                contract_no = str(row.get('contract_no', '')).strip()
                if Contract.objects.filter(contract_no=contract_no).exists():
                    error_list.append({'row': idx + 2, 'error': f'合同编号 {contract_no} 已存在'})
                    continue

                amount = row.get('amount', 0)
                if pd.isna(amount) or float(amount) <= 0:
                    error_list.append({'row': idx + 2, 'error': '金额必须大于零'})
                    continue

                Contract.objects.create(
                    contract_no=contract_no,
                    title=str(row.get('title', '')).strip(),
                    client_name=str(row.get('client_name', '')).strip(),
                    client_contact=str(row.get('client_contact', '')).strip() if pd.notna(row.get('client_contact')) else '',
                    contract_type=str(row.get('contract_type', '')).strip() if pd.notna(row.get('contract_type')) else '',
                    product_type=str(row.get('product_type', '')).strip() if pd.notna(row.get('product_type')) else '',
                    amount=float(amount),
                    currency=str(row.get('currency', 'CNY')).strip() if pd.notna(row.get('currency')) else 'CNY',
                    region=str(row.get('region', '')).strip() if pd.notna(row.get('region')) else '',
                    sign_date=row.get('sign_date') if pd.notna(row.get('sign_date')) else None,
                    start_date=row.get('start_date') if pd.notna(row.get('start_date')) else None,
                    end_date=row.get('end_date') if pd.notna(row.get('end_date')) else None,
                    status=str(row.get('status', 'draft')).strip() if pd.notna(row.get('status')) else 'draft',
                    salesperson=str(row.get('salesperson', '')).strip() if pd.notna(row.get('salesperson')) else '',
                    department=str(row.get('department', '')).strip() if pd.notna(row.get('department')) else '',
                    description=str(row.get('description', '')).strip() if pd.notna(row.get('description')) else '',
                    created_by=request.user,
                )
                contract = Contract.objects.get(contract_no=contract_no)
                update_contract_metrics(contract)
                success_count += 1
            except Exception as e:
                error_list.append({'row': idx + 2, 'error': str(e)})

        return success_response(
            data={
                'success_count': success_count,
                'error_count': len(error_list),
                'errors': error_list,
            },
            message=f'导入完成：成功{success_count}条，失败{len(error_list)}条',
        )

    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return error_response(message='请选择要删除的合同')
        deleted_count = Contract.objects.filter(id__in=ids).update(is_deleted=True)
        return success_response(
            data={'deleted_count': deleted_count},
            message=f'已删除{deleted_count}条合同',
        )

    @action(detail=False, methods=['get'])
    def import_template(self, request):
        columns = [
            {'key': 'contract_no', 'label': '合同编号', 'width': 20},
            {'key': 'title', 'label': '合同标题', 'width': 30},
            {'key': 'client_name', 'label': '客户名称', 'width': 20},
            {'key': 'client_contact', 'label': '客户联系人', 'width': 15},
            {'key': 'contract_type', 'label': '合同类型', 'width': 15},
            {'key': 'product_type', 'label': '产品类型', 'width': 15},
            {'key': 'amount', 'label': '合同金额', 'width': 15},
            {'key': 'currency', 'label': '货币(CNY/USD/EUR)', 'width': 15},
            {'key': 'region', 'label': '区域', 'width': 15},
            {'key': 'sign_date', 'label': '签订日期(YYYY-MM-DD)', 'width': 20},
            {'key': 'start_date', 'label': '开始日期(YYYY-MM-DD)', 'width': 20},
            {'key': 'end_date', 'label': '结束日期(YYYY-MM-DD)', 'width': 20},
            {'key': 'status', 'label': '状态(draft/active/completed)', 'width': 20},
            {'key': 'salesperson', 'label': '销售人员', 'width': 15},
            {'key': 'department', 'label': '部门', 'width': 15},
            {'key': 'description', 'label': '描述', 'width': 30},
        ]
        return export_to_excel([], columns, filename='contract_import_template.xlsx')

    @action(detail=False, methods=['get'])
    def export_pdf(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = ContractListSerializer(queryset, many=True)
        columns = [
            {'key': 'contract_no', 'label': '合同编号', 'pdf_width': 80},
            {'key': 'title', 'label': '合同标题', 'pdf_width': 100},
            {'key': 'client_name', 'label': '客户名称', 'pdf_width': 80},
            {'key': 'amount', 'label': '合同金额', 'pdf_width': 60},
            {'key': 'status_display', 'label': '状态', 'pdf_width': 50},
            {'key': 'sign_date', 'label': '签订日期', 'pdf_width': 70},
        ]
        return export_to_pdf(serializer.data, columns, title='销售合同数据报表', filename='contracts.pdf')
