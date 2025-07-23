from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    # Service Categories
    path('categories/', views.ServiceCategoryListView.as_view(), name='category-list'),
    
    # Service Management
    path('services/', views.ServiceListView.as_view(), name='service-list'),
    path('services/create/', views.ServiceCreateView.as_view(), name='service-create'),
    path('services/<int:pk>/', views.ServiceDetailView.as_view(), name='service-detail'),
    
    # Worker Management
    path('workers/', views.WorkerListView.as_view(), name='worker-list'),
    path('workers/create/', views.WorkerCreateView.as_view(), name='worker-create'),
    path('workers/<int:pk>/', views.WorkerDetailView.as_view(), name='worker-detail'),
    
    # Service Records Management
    path('records/', views.ServiceRecordListView.as_view(), name='record-list'),
    path('records/create/', views.ServiceRecordCreateView.as_view(), name='record-create'),
    path('records/<int:pk>/', views.ServiceRecordDetailView.as_view(), name='record-detail'),
    
    # Payment Management
    path('records/<int:record_id>/update-payment/', views.update_payment, name='update-payment'),
    
    # Reports and Analytics
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reports/summary/', views.service_records_summary, name='records-summary'),
    path('reports/performance/', views.worker_performance_report, name='performance-report'),
]
