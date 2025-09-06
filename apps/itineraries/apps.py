# apps/itineraries/apps.py
from django.apps import AppConfig

class ItinerariesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.itineraries'     # PHẢI đúng đầy đủ path tới app
    verbose_name = 'Itineraries'
