from django.contrib import admin
from django import forms
from .models import UserProfile


class UserProfileAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Always set up the subcategory field as a choice field
        if self.instance and self.instance.pk and self.instance.business_type:
            # Editing existing object with business type
            subcategory_choices = self.instance.get_subcategory_choices()
            self.fields['business_subcategory'] = forms.ChoiceField(
                choices=[('', '--- Select Subcategory ---')] + subcategory_choices,
                required=False,
                help_text="Specific subcategory of your business type"
            )
        else:
            # For new objects, show all possible subcategories grouped
            all_choices = [('', '--- Select Business Type First ---')]
            
            # Add all subcategories from all business types for now
            temp_profile = UserProfile()
            for business_type, _ in UserProfile.BUSINESS_TYPE_CHOICES:
                temp_profile.business_type = business_type
                subcategories = temp_profile.get_subcategory_choices()
                for value, display in subcategories:
                    all_choices.append((value, display))
            
            self.fields['business_subcategory'] = forms.ChoiceField(
                choices=all_choices,
                required=False,
                help_text="Select a business type first to see relevant subcategories"
            )
    
    class Meta:
        model = UserProfile
        fields = '__all__'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileAdminForm
    list_display = (
        'full_name',
        'business_name',
        'email',
        'phone',
        'created_at'
    )
    list_filter = (
        'business_type',
        'business_subcategory',
        'business_province',
        'is_complete',
        'employee_count',
        'monthly_revenue_range',
        'created_at'
    )
    search_fields = (
        'first_name',
        'last_name',
        'full_name',
        'business_name',
        'user__email',
        'user__phone',
        'business_city',
        'business_province'
    )
    readonly_fields = (
        'user',
        'email',
        'phone',
        'full_name',
        'business_location',
        'is_complete',
        'created_at',
        'updated_at'
    )
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'email', 'phone')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'full_name')
        }),
        ('Business Information', {
            'fields': ('business_name',)
        }),
        ('Business Details', {
            'fields': (
                'business_type',
                'business_subcategory',
                'business_city',
                'business_province',
                'business_location'
            )
        }),
        ('Optional Business Information', {
            'fields': ('employee_count', 'monthly_revenue_range'),
            'classes': ('collapse',)
        }),
        ('Status & Dates', {
            'fields': ('is_complete', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    ordering = ('-created_at',)
    
    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email Address'
    
    def phone(self, obj):
        return obj.user.phone
    phone.short_description = 'Phone Number'
    
    def has_add_permission(self, request):
        # Profiles should be created automatically when users register
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of profiles from admin
        return False
    
    class Media:
        js = ('profiles/js/business_subcategory.js',)
