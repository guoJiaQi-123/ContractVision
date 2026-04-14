from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import config_views, views
from .backup_views import BackupCreateView, BackupDeleteView, BackupListView, BackupRestoreView
from .integration_views import IntegrationConfigViewSet

router = DefaultRouter()
router.register('v1/system/logs', views.OperationLogViewSet, basename='operation-log')
router.register('v1/system/integrations', IntegrationConfigViewSet, basename='integration-config')
router.register('v1/system/data-permissions', config_views.DataPermissionRuleViewSet, basename='data-permission-rule')
router.register('v1/system/alert-rules', config_views.AlertRuleViewSet, basename='alert-rule')
router.register('v1/system/alerts', config_views.AlertMessageViewSet, basename='alert-message')
router.register('v1/system/sales-targets', config_views.SalesTargetViewSet, basename='sales-target')
router.register('v1/system/dashboards', config_views.DashboardConfigViewSet, basename='dashboard-config')
router.register('v1/system/templates', config_views.DataTemplateViewSet, basename='data-template')
router.register('v1/system/currency-rates', config_views.CurrencyRateViewSet, basename='currency-rate')
router.register('v1/system/stamp-tax-rules', config_views.StampTaxRuleViewSet, basename='stamp-tax-rule')

urlpatterns = [
    path('v1/system/backup/', BackupListView.as_view(), name='backup-list'),
    path('v1/system/backup/create/', BackupCreateView.as_view(), name='backup-create'),
    path('v1/system/backup/restore/', BackupRestoreView.as_view(), name='backup-restore'),
    path('v1/system/backup/delete/', BackupDeleteView.as_view(), name='backup-delete'),
    path('v1/system/mobile-dashboard/', config_views.MobileDashboardView.as_view(), name='mobile-dashboard'),
    path('', include(router.urls)),
]
