# apps.py
from django.apps import AppConfig

class ReviewsConfig(AppConfig):
    name = 'apps.reviews'
    def ready(self):
        from . import signals  # noqa