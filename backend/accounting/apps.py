# Accounting Module

from django.apps import AppConfig


class AccountingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounting'
    
    def ready(self):
        """Import signals when the app is ready"""
        import accounting.signals
