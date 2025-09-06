from django.db import models
from django.conf import settings
from apps.places.models import Place

class Review(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='reviews')
    user  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()  # 1..5
    comment = models.TextField(blank=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)