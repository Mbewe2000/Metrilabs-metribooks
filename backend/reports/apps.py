from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reports'
    verbose_name = 'Reports and Analytics'
    
    def ready(self):
        """
        Import signals when the app is ready
        """
        import reports.signals
