from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'snapshots', views.ReportSnapshotViewSet, basename='reportsnapshot')
router.register(r'templates', views.ReportTemplateViewSet, basename='reporttemplate')
router.register(r'metrics', views.BusinessMetricViewSet, basename='businessmetric')

app_name = 'reports'

urlpatterns = [
    # Include ViewSet routes
    path('', include(router.urls)),
    
    # Report Generation Endpoints
    path('generate/', views.ReportGenerationView.as_view(), name='generate-report'),
    
    # Quick Report Views
    path('profit-loss/', views.profit_loss_summary, name='profit-loss'),
    path('cash-flow/', views.cash_flow_summary, name='cash-flow'),
    path('sales-trends/', views.sales_trends, name='sales-trends'),
    path('expense-trends/', views.expense_trends, name='expense-trends'),
    path('tax-summary/', views.tax_summary, name='tax-summary'),
    path('business-overview/', views.business_overview, name='business-overview'),
    
    # Analytics Dashboard
    path('dashboard/', views.analytics_dashboard, name='analytics-dashboard'),
]
