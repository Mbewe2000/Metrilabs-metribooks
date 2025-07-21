from django.contrib import admin
from django_db_logger.models import StatusLog


class StatusLogAdmin(admin.ModelAdmin):
    list_display = ['logger_name', 'level', 'msg', 'create_datetime', 'trace']
    list_filter = ['logger_name', 'level', 'create_datetime']
    search_fields = ['msg', 'logger_name']
    readonly_fields = ['logger_name', 'level', 'msg', 'create_datetime', 'trace']
    ordering = ['-create_datetime']
    
    # Custom filtering
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.order_by('-create_datetime')
    
    # Make logs read-only
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    # Custom display methods
    def colored_level(self, obj):
        colors = {
            'DEBUG': 'gray',
            'INFO': 'blue',
            'WARNING': 'orange',
            'ERROR': 'red',
            'CRITICAL': 'darkred',
        }
        color = colors.get(obj.level, 'black')
        return f'<span style="color: {color}; font-weight: bold">{obj.level}</span>'
    colored_level.short_description = 'Level'
    colored_level.allow_tags = True
    
    # Custom fieldsets for better organization
    fieldsets = (
        ('Log Information', {
            'fields': ('logger_name', 'level', 'create_datetime')
        }),
        ('Message', {
            'fields': ('msg',)
        }),
        ('Stack Trace', {
            'fields': ('trace',),
            'classes': ('collapse',)
        }),
    )


# Unregister the default admin and register our custom one
try:
    admin.site.unregister(StatusLog)
except admin.sites.NotRegistered:
    pass

admin.site.register(StatusLog, StatusLogAdmin)
