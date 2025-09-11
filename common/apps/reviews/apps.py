from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common.apps.reviews'
    
    def ready(self):
        import apps.reviews.signals