from django.urls import path
from .views import EmployeeViewSet

urlpatterns = [
    # Employee CRUD operations
    path('employees/', EmployeeViewSet.as_view({'get': 'list', 'post': 'create'}), name='employee-list'),
    path('employees/<int:pk>/', EmployeeViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='employee-detail'),
    
    # Custom employee endpoints
    path('employees/active/', EmployeeViewSet.as_view({'get': 'active_employees'}), name='employee-active'),
    path('employees/full-time/', EmployeeViewSet.as_view({'get': 'full_time_employees'}), name='employee-full-time'),
    path('employees/part-time/', EmployeeViewSet.as_view({'get': 'part_time_employees'}), name='employee-part-time'),
    path('employees/<int:pk>/activate/', EmployeeViewSet.as_view({'patch': 'activate'}), name='employee-activate'),
    path('employees/<int:pk>/deactivate/', EmployeeViewSet.as_view({'patch': 'deactivate'}), name='employee-deactivate'),
]
