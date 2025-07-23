from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API URL patterns
urlpatterns = [
    # Expense Management
    path('expense-categories/', views.ExpenseCategoryListView.as_view(), name='expense-categories'),
    path('expenses/', views.ExpenseListView.as_view(), name='expense-list'),
    path('expenses/create/', views.ExpenseCreateView.as_view(), name='expense-create'),
    path('expenses/<uuid:pk>/', views.ExpenseDetailView.as_view(), name='expense-detail'),
    
    # Asset Management
    path('asset-categories/', views.AssetCategoryListView.as_view(), name='asset-categories'),
    path('assets/', views.AssetListView.as_view(), name='asset-list'),
    path('assets/create/', views.AssetCreateView.as_view(), name='asset-create'),
    path('assets/<uuid:pk>/', views.AssetDetailView.as_view(), name='asset-detail'),
    
    # Income Tracking
    path('income/', views.IncomeRecordListView.as_view(), name='income-list'),
    
    # Tax Management
    path('turnover-tax/', views.TurnoverTaxRecordListView.as_view(), name='turnover-tax-list'),
    path('turnover-tax/calculate/', views.calculate_turnover_tax, name='calculate-turnover-tax'),
    
    # Reports
    path('reports/profit-loss/', views.profit_loss_report, name='profit-loss-report'),
    path('reports/turnover-tax/', views.turnover_tax_report, name='turnover-tax-report'),
    path('reports/expense-analysis/', views.expense_analysis_report, name='expense-analysis-report'),
    
    # Dashboard
    path('dashboard/', views.financial_dashboard, name='financial-dashboard'),
]
