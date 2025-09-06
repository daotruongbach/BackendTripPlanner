# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count
from .models import Review
from apps.places.models import Place

@receiver([post_save, post_delete], sender=Review)
def update_place_rating(sender, instance, **kwargs):
    place = instance.place
    agg = place.reviews.filter(is_approved=True).aggregate(avg=Avg('rating'), cnt=Count('id'))
    place.rating_avg = agg['avg'] or 0
    place.reviews_count = agg['cnt'] or 0
    place.save(update_fields=['rating_avg','reviews_count'])