from django.apps import AppConfig


class EmployeesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'employees'
    verbose_name = 'Employee Management'
    
    def ready(self):
        """Import signals when the app is ready"""
        import employees.signals
