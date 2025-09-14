# apps/posts/apps.py
from django.apps import AppConfig

class PostsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.posts"

    def ready(self):
        # nạp signal khi app khởi động
        from . import signals  # noqa: F401