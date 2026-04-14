from django.urls import path

from .advanced_views import (
    DashboardDataView,
    DrilldownAnalysisView,
    SalesTargetProgressView,
    TaxAnalysisView,
    TeamPerformanceView,
)
from . import views
from .prediction_views import AnomalyDetectionView, CustomerValueView, SalesPredictionView
from .report_views import ReportExportView, ReportGenerateView

urlpatterns = [
    path('v1/analytics/dashboard/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
    path('v1/analytics/trend/', views.ContractTrendView.as_view(), name='contract-trend'),
    path('v1/analytics/region/', views.RegionDistributionView.as_view(), name='region-distribution'),
    path('v1/analytics/status/', views.StatusDistributionView.as_view(), name='status-distribution'),
    path('v1/analytics/top-clients/', views.TopClientsView.as_view(), name='top-clients'),
    path('v1/analytics/salesperson-ranking/', views.SalespersonRankingView.as_view(), name='salesperson-ranking'),
    path('v1/analytics/product/', views.ProductDistributionView.as_view(), name='product-distribution'),
    path('v1/analytics/monthly-trend/', views.MonthlyTrendView.as_view(), name='monthly-trend'),
    path('v1/analytics/department-ranking/', views.DepartmentRankingView.as_view(), name='department-ranking'),
    path('v1/analytics/overview-summary/', views.OverviewSummaryView.as_view(), name='overview-summary'),
    path('v1/analytics/report/generate/', ReportGenerateView.as_view(), name='report-generate'),
    path('v1/analytics/report/export/', ReportExportView.as_view(), name='report-export'),
    path('v1/analytics/prediction/', SalesPredictionView.as_view(), name='sales-prediction'),
    path('v1/analytics/anomaly-detection/', AnomalyDetectionView.as_view(), name='anomaly-detection'),
    path('v1/analytics/customer-value/', CustomerValueView.as_view(), name='customer-value'),
    path('v1/analytics/target-progress/', SalesTargetProgressView.as_view(), name='target-progress'),
    path('v1/analytics/dashboard-data/', DashboardDataView.as_view(), name='dashboard-data'),
    path('v1/analytics/drilldown/', DrilldownAnalysisView.as_view(), name='drilldown-analysis'),
    path('v1/analytics/team-performance/', TeamPerformanceView.as_view(), name='team-performance'),
    path('v1/analytics/tax-analysis/', TaxAnalysisView.as_view(), name='tax-analysis'),
]
