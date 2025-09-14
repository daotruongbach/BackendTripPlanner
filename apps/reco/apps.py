from django.apps import AppConfig
class RecoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reco"
    def ready(self):
        from . import signals # noqa