from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common.apps.analytics'
    verbose_name = 'Analytics & Usage Tracking'
    
    def ready(self):
        # Import signals if any
        pass
