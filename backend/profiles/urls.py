from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    # Profile management endpoints
    path('profile/', views.UserProfileView.as_view(), name='profile-detail'),
    path('profile/update/', views.UserProfileUpdateView.as_view(), name='profile-update'),
    path('profile/summary/', views.profile_summary, name='profile-summary'),
    path('profile/completion/', views.profile_completion_status, name='profile-completion'),
    # Business subcategories endpoint
    path('business/subcategories/', views.business_subcategories, name='business-subcategories'),
]
