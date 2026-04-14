from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import advanced_views, views

router = DefaultRouter()
router.register('v1/contracts', views.ContractViewSet, basename='contract')
router.register('v1/contracts/payment-plans', advanced_views.PaymentPlanViewSet, basename='payment-plan')
router.register('v1/contracts/milestones', advanced_views.ContractMilestoneViewSet, basename='contract-milestone')
router.register('v1/contracts/change-requests', advanced_views.ContractChangeRequestViewSet, basename='contract-change-request')
router.register('v1/contracts/approval-processes', advanced_views.ApprovalProcessViewSet, basename='approval-process')
router.register('v1/contracts/approval-requests', advanced_views.ApprovalRequestViewSet, basename='approval-request')

urlpatterns = [
    path('v1/contracts/quality-report/', advanced_views.ContractQualityReportView.as_view(), name='contract-quality-report'),
    path('v1/contracts/duplicate-scan/', advanced_views.DuplicateContractScanView.as_view(), name='contract-duplicate-scan'),
    path('', include(router.urls)),
]
