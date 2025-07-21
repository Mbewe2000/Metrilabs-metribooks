from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Product Category URLs
    path('categories/', views.ProductCategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', views.ProductCategoryDetailView.as_view(), name='category-detail'),
    
    # Product URLs
    path('products/', views.ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    
    # Inventory URLs
    path('inventory/<int:product_id>/', views.ProductInventoryUpdateView.as_view(), name='inventory-update'),
    
    # Stock Movement URLs
    path('stock-movements/', views.StockMovementListCreateView.as_view(), name='stock-movement-list-create'),
    
    # Report URLs
    path('reports/inventory-summary/', views.inventory_summary_report, name='inventory-summary-report'),
    path('reports/low-stock-alerts/', views.low_stock_alerts, name='low-stock-alerts'),
    path('reports/inventory-valuation/', views.inventory_valuation_report, name='inventory-valuation-report'),
]
