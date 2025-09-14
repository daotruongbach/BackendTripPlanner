# apps/reviews/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Review

@receiver(post_save, sender=Review)
def _recalc_on_save(sender, instance: Review, **kwargs):
    Review.recalc_place_stats(instance.place)

@receiver(post_delete, sender=Review)
def _recalc_on_delete(sender, instance: Review, **kwargs):
    Review.recalc_place_stats(instance.place)
