from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'phone', 'business_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'email_verified', 'phone_verified')
    readonly_fields = ('date_joined', 'last_login', 'business_name', 'full_name')
    fieldsets = (
        (None, {'fields': ('email', 'phone', 'password')}),
        ('Profile Information', {'fields': ('business_name', 'full_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Verification', {'fields': ('email_verified', 'phone_verified')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'phone', 'profile__business_name', 'profile__first_name', 'profile__last_name')
    ordering = ('email',)
    
    def business_name(self, obj):
        """Display business name from related profile"""
        try:
            if hasattr(obj, 'profile') and obj.profile and obj.profile.business_name:
                return obj.profile.business_name
            return 'No business name'
        except:
            return 'No profile'
    business_name.short_description = 'Business Name'
    business_name.admin_order_field = 'profile__business_name'
    
    def full_name(self, obj):
        """Display full name from related profile"""
        try:
            if hasattr(obj, 'profile') and obj.profile and obj.profile.full_name:
                return obj.profile.full_name
            return 'No name'
        except:
            return 'No profile'
    full_name.short_description = 'Full Name'
    full_name.admin_order_field = 'profile__full_name'


admin.site.register(CustomUser, CustomUserAdmin)
