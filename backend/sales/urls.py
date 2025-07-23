from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # Sales Management
    path('sales/', views.SaleListView.as_view(), name='sale-list'),
    path('sales/create/', views.SaleCreateView.as_view(), name='sale-create'),
    path('sales/<uuid:pk>/', views.SaleDetailView.as_view(), name='sale-detail'),
    
    # Sale Items
    path('sales/<uuid:sale_id>/items/', views.SaleItemListView.as_view(), name='sale-items'),
    
    # Receipt Generation
    path('sales/<uuid:sale_id>/receipt/', views.generate_receipt, name='generate-receipt'),
    
    # Reports and Analytics
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reports/summary/', views.sales_summary, name='sales-summary'),
    path('reports/', views.SalesReportListView.as_view(), name='reports-list'),
]
