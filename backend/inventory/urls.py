from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Product management endpoints
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/create/', views.ProductCreateView.as_view(), name='product-create'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    
    # Inventory management endpoints
    path('products/<int:product_id>/adjust-stock/', views.StockAdjustmentView.as_view(), name='stock-adjustment'),
    
    # Stock movement endpoints
    path('stock-movements/', views.StockMovementListView.as_view(), name='stock-movement-list'),
    
    # Category endpoints
    path('categories/', views.ProductCategoryListView.as_view(), name='category-list'),
    
    # Alert endpoints
    path('alerts/', views.StockAlertListView.as_view(), name='alert-list'),
    path('alerts/<int:alert_id>/resolve/', views.resolve_stock_alert, name='alert-resolve'),
    
    # Dashboard and reports endpoints
    path('dashboard/', views.inventory_dashboard, name='dashboard'),
    path('reports/stock-summary/', views.stock_summary_report, name='stock-summary-report'),
    path('reports/valuation/', views.inventory_valuation_report, name='valuation-report'),
]
