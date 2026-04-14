from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.users.permissions import IsAdmin, IsOperator
from core.response import error_response, success_response

from .models import (
    ApprovalProcess,
    ApprovalRequest,
    Contract,
    ContractChangeRequest,
    ContractMilestone,
    PaymentPlan,
)
from .serializers import (
    ApprovalProcessSerializer,
    ApprovalRequestSerializer,
    ContractChangeRequestSerializer,
    ContractCreateSerializer,
    ContractMilestoneSerializer,
    ContractSerializer,
    PaymentPlanSerializer,
)
from .services import find_duplicate_contracts, update_contract_metrics


def _sync_payment_status(contract):
    plans = list(contract.payment_plans.all())
    if not plans:
        return
    paid_count = sum(1 for item in plans if item.status == PaymentPlan.Status.PAID)
    if paid_count == len(plans):
        contract.payment_status = Contract.PaymentStatus.PAID
    elif paid_count > 0:
        contract.payment_status = Contract.PaymentStatus.PARTIAL
    else:
        contract.payment_status = Contract.PaymentStatus.UNPAID
    contract.save(update_fields=['payment_status', 'updated_at'])


def _sync_delivery_status(contract):
    milestones = list(contract.milestones.filter(node_type=ContractMilestone.NodeType.DELIVERY))
    if not milestones:
        return
    completed_count = sum(1 for item in milestones if item.status == ContractMilestone.Status.COMPLETED)
    if completed_count == len(milestones):
        contract.delivery_status = Contract.DeliveryStatus.DELIVERED
    elif completed_count > 0:
        contract.delivery_status = Contract.DeliveryStatus.IN_PROGRESS
    else:
        contract.delivery_status = Contract.DeliveryStatus.PENDING
    contract.save(update_fields=['delivery_status', 'updated_at'])


class StandardizedModelViewSet(viewsets.ModelViewSet):
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


class PaymentPlanViewSet(StandardizedModelViewSet):
    queryset = PaymentPlan.objects.select_related('contract').all()
    serializer_class = PaymentPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy', 'mark_paid'):
            return [IsAuthenticated(), IsOperator()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        contract_id = self.request.query_params.get('contract')
        overdue_only = self.request.query_params.get('overdue_only')
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        if overdue_only == '1':
            today = timezone.now().date()
            queryset = queryset.filter(paid_date__isnull=True, due_date__lt=today)
        return queryset.order_by('due_date')

    def perform_create(self, serializer):
        plan = serializer.save()
        _sync_payment_status(plan.contract)

    def perform_update(self, serializer):
        plan = serializer.save()
        _sync_payment_status(plan.contract)

    def perform_destroy(self, instance):
        contract = instance.contract
        instance.delete()
        _sync_payment_status(contract)

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        plan = self.get_object()
        plan.status = PaymentPlan.Status.PAID
        plan.paid_date = request.data.get('paid_date') or timezone.now().date()
        plan.actual_amount = request.data.get('actual_amount') or plan.amount
        plan.voucher_no = request.data.get('voucher_no', plan.voucher_no)
        plan.save()
        _sync_payment_status(plan.contract)
        return success_response(data=PaymentPlanSerializer(plan).data, message='付款状态更新成功')

    @action(detail=False, methods=['get'])
    def overview(self, request):
        queryset = self.get_queryset()
        today = timezone.now().date()
        data = {
            'pending_count': queryset.filter(status=PaymentPlan.Status.PENDING).count(),
            'paid_count': queryset.filter(status=PaymentPlan.Status.PAID).count(),
            'overdue_count': queryset.filter(paid_date__isnull=True, due_date__lt=today).count(),
            'severe_overdue_count': queryset.filter(paid_date__isnull=True, due_date__lt=today - timedelta(days=30)).count(),
        }
        return success_response(data=data)


class ContractMilestoneViewSet(StandardizedModelViewSet):
    queryset = ContractMilestone.objects.select_related('contract').all()
    serializer_class = ContractMilestoneSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy', 'mark_complete'):
            return [IsAuthenticated(), IsOperator()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        contract_id = self.request.query_params.get('contract')
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        return queryset.order_by('planned_date', 'id')

    def perform_create(self, serializer):
        milestone = serializer.save()
        _sync_delivery_status(milestone.contract)

    def perform_update(self, serializer):
        milestone = serializer.save()
        _sync_delivery_status(milestone.contract)

    def perform_destroy(self, instance):
        contract = instance.contract
        instance.delete()
        _sync_delivery_status(contract)

    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        milestone = self.get_object()
        milestone.status = ContractMilestone.Status.COMPLETED
        milestone.actual_date = request.data.get('actual_date') or timezone.now().date()
        milestone.remark = request.data.get('remark', milestone.remark)
        milestone.evidences = request.data.get('evidences', milestone.evidences)
        milestone.save()
        _sync_delivery_status(milestone.contract)
        return success_response(data=ContractMilestoneSerializer(milestone).data, message='履约节点已完成')


class ContractChangeRequestViewSet(StandardizedModelViewSet):
    queryset = ContractChangeRequest.objects.select_related('contract', 'requested_by', 'approved_by').all()
    serializer_class = ContractChangeRequestSerializer
    permission_classes = [IsAuthenticated, IsOperator]

    def get_queryset(self):
        queryset = super().get_queryset()
        contract_id = self.request.query_params.get('contract')
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        return queryset

    def perform_create(self, serializer):
        contract = Contract.objects.get(pk=self.request.data.get('contract'))
        before_snapshot = ContractSerializer(contract).data
        serializer.save(requested_by=self.request.user, before_snapshot=before_snapshot)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        change_request = self.get_object()
        if change_request.status != ContractChangeRequest.Status.PENDING:
            return error_response(message='该变更申请已处理')

        process = ApprovalProcess.objects.filter(
            action_type=ApprovalProcess.ActionType.CHANGE,
            is_active=True,
            min_amount__lte=change_request.contract.base_amount,
        ).order_by('-min_amount').first()
        if process:
            ApprovalRequest.objects.create(
                contract=change_request.contract,
                process=process,
                action_type=ApprovalProcess.ActionType.CHANGE,
                title=f'合同变更审批 - {change_request.contract.contract_no}',
                request_payload={
                    'change_request_id': change_request.id,
                    'fields': change_request.after_snapshot,
                },
                requested_by=change_request.requested_by,
            )
            return success_response(message='已提交审批流程')

        with transaction.atomic():
            serializer = ContractCreateSerializer(
                change_request.contract,
                data=change_request.after_snapshot,
                partial=True,
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            update_contract_metrics(change_request.contract)
            change_request.status = ContractChangeRequest.Status.APPROVED
            change_request.approved_by = request.user
            change_request.approved_at = timezone.now()
            change_request.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
        return success_response(data=ContractChangeRequestSerializer(change_request).data, message='变更已审批通过')

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        change_request = self.get_object()
        change_request.status = ContractChangeRequest.Status.REJECTED
        change_request.approved_by = request.user
        change_request.approved_at = timezone.now()
        change_request.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
        return success_response(data=ContractChangeRequestSerializer(change_request).data, message='变更申请已驳回')


class ApprovalProcessViewSet(StandardizedModelViewSet):
    queryset = ApprovalProcess.objects.select_related('created_by').all()
    serializer_class = ApprovalProcessSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ApprovalRequestViewSet(StandardizedModelViewSet):
    queryset = ApprovalRequest.objects.select_related('contract', 'process', 'requested_by', 'reviewed_by').all()
    serializer_class = ApprovalRequestSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        approval = self.get_object()
        if approval.status != ApprovalRequest.Status.PENDING:
            return error_response(message='审批申请已处理')

        with transaction.atomic():
            contract = approval.contract
            if approval.action_type == ApprovalProcess.ActionType.CREATE and contract:
                contract.approval_status = Contract.ApprovalStatus.APPROVED
                contract.save(update_fields=['approval_status', 'updated_at'])
            elif approval.action_type == ApprovalProcess.ActionType.UPDATE and contract:
                serializer = ContractCreateSerializer(contract, data=approval.request_payload, partial=True, context={'request': request})
                serializer.is_valid(raise_exception=True)
                serializer.save()
                contract.approval_status = Contract.ApprovalStatus.APPROVED
                contract.save(update_fields=['approval_status', 'updated_at'])
            elif approval.action_type == ApprovalProcess.ActionType.DELETE and contract:
                contract.delete()
            elif approval.action_type == ApprovalProcess.ActionType.CHANGE and contract:
                change_request_id = approval.request_payload.get('change_request_id')
                change_request = ContractChangeRequest.objects.filter(pk=change_request_id).first()
                serializer = ContractCreateSerializer(contract, data=approval.request_payload.get('fields', {}), partial=True, context={'request': request})
                serializer.is_valid(raise_exception=True)
                serializer.save()
                if change_request:
                    change_request.status = ContractChangeRequest.Status.APPROVED
                    change_request.approved_by = request.user
                    change_request.approved_at = timezone.now()
                    change_request.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
                contract.approval_status = Contract.ApprovalStatus.APPROVED
                contract.save(update_fields=['approval_status', 'updated_at'])

            approval.status = ApprovalRequest.Status.APPROVED
            approval.reviewed_by = request.user
            approval.reviewed_at = timezone.now()
            approval.review_logs = approval.review_logs + [{
                'step': approval.current_step,
                'action': 'approved',
                'reviewer': request.user.username,
                'comment': request.data.get('comment', ''),
                'time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            }]
            approval.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_logs', 'updated_at'])

        return success_response(data=ApprovalRequestSerializer(approval).data, message='审批已通过')

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        approval = self.get_object()
        if approval.status != ApprovalRequest.Status.PENDING:
            return error_response(message='审批申请已处理')
        if approval.contract:
            approval.contract.approval_status = Contract.ApprovalStatus.REJECTED
            approval.contract.save(update_fields=['approval_status', 'updated_at'])
        approval.status = ApprovalRequest.Status.REJECTED
        approval.reviewed_by = request.user
        approval.reviewed_at = timezone.now()
        approval.review_logs = approval.review_logs + [{
            'step': approval.current_step,
            'action': 'rejected',
            'reviewer': request.user.username,
            'comment': request.data.get('comment', ''),
            'time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        }]
        approval.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_logs', 'updated_at'])
        return success_response(data=ApprovalRequestSerializer(approval).data, message='审批已驳回')


class ContractQualityReportView(APIView):
    permission_classes = [IsAuthenticated, IsOperator]

    def get(self, request):
        queryset = Contract.objects.all()
        contract_id = request.query_params.get('contract')
        if contract_id:
            queryset = queryset.filter(pk=contract_id)

        results = []
        for contract in queryset[:500]:
            update_contract_metrics(contract)
            results.append({
                'id': contract.id,
                'contract_no': contract.contract_no,
                'title': contract.title,
                'quality_score': contract.quality_score,
                'quality_issues': contract.quality_issues,
            })

        passing_count = sum(1 for item in results if item['quality_score'] >= 80)
        data = {
            'summary': {
                'total': len(results),
                'passing_count': passing_count,
                'passing_rate': round(passing_count / len(results) * 100, 2) if results else 0,
            },
            'list': results,
        }
        return success_response(data=data)


class DuplicateContractScanView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        queryset = Contract.objects.all()
        data = find_duplicate_contracts(queryset)
        return success_response(data={'groups': data, 'group_count': len(data)})

    def post(self, request):
        primary_id = request.data.get('primary_id')
        duplicate_ids = request.data.get('duplicate_ids', [])
        if not primary_id or not duplicate_ids:
            return error_response(message='请提供主合同和重复合同列表')

        primary = Contract.objects.filter(pk=primary_id).first()
        if not primary:
            return error_response(message='主合同不存在')

        for duplicate in Contract.objects.filter(pk__in=duplicate_ids).exclude(pk=primary.id):
            if duplicate.description and duplicate.description not in primary.description:
                primary.description = '\n'.join(filter(None, [primary.description, duplicate.description]))
            duplicate.delete()
        primary.save(update_fields=['description', 'updated_at'])
        update_contract_metrics(primary)
        return success_response(data=ContractSerializer(primary).data, message='重复合同已合并')
