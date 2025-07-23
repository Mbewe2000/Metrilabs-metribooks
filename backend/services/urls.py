from django.urls import path
from .views import ServiceCategoryViewSet, ServiceViewSet, WorkRecordViewSet

urlpatterns = [
    # Service Categories
    path('categories/', ServiceCategoryViewSet.as_view({'get': 'list', 'post': 'create'}), name='servicecategory-list'),
    path('categories/<int:pk>/', ServiceCategoryViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='servicecategory-detail'),
    
    # Services
    path('services/', ServiceViewSet.as_view({'get': 'list', 'post': 'create'}), name='service-list'),
    path('services/<int:pk>/', ServiceViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='service-detail'),
    path('services/by-category/<int:category_id>/', ServiceViewSet.as_view({'get': 'by_category'}), name='service-by-category'),
    
    # Work Records
    path('work-records/', WorkRecordViewSet.as_view({'get': 'list', 'post': 'create'}), name='workrecord-list'),
    path('work-records/<int:pk>/', WorkRecordViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='workrecord-detail'),
    path('work-records/by-employee/<int:employee_id>/', WorkRecordViewSet.as_view({'get': 'by_employee'}), name='workrecord-by-employee'),
    path('work-records/by-service/<int:service_id>/', WorkRecordViewSet.as_view({'get': 'by_service'}), name='workrecord-by-service'),
    path('work-records/daily-summary/', WorkRecordViewSet.as_view({'get': 'daily_summary'}), name='workrecord-daily-summary'),
    path('work-records/employee-performance/', WorkRecordViewSet.as_view({'get': 'employee_summary'}), name='workrecord-employee-performance'),
]
