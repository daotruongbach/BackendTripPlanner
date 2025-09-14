from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.posts.models import Reaction
from apps.reviews.models import Review, ReviewStatus
from apps.itineraries.models import ItineraryItem
from .services.prefs import bump_pref

def _categories_from_post(post):
    cats = set()
    if getattr(post, "place", None) and post.place and post.place.category:
        cats.add(post.place.category)
    if getattr(post, "itinerary", None) and post.itinerary:
        for it in post.itinerary.items.select_related("place"):
            if it.place and it.place.category:
                cats.add(it.place.category)
    return cats

@receiver(post_save, sender=Reaction)
def on_reaction_created(sender, instance, created, **kwargs):
    if not created: return
    for cat in _categories_from_post(instance.post):
        bump_pref(instance.user, cat, +2.0)

@receiver(post_save, sender=Review)
def on_review_approved(sender, instance, created, **kwargs):
    if instance.status != ReviewStatus.APPROVED: return
    place = getattr(instance, "place", None)
    if place and place.category:
        bump_pref(instance.user, place.category, float(instance.rating) - 3.0)

@receiver(post_save, sender=ItineraryItem)
def on_itinerary_item_added(sender, instance, created, **kwargs):
    if not created: return
    place = getattr(instance, "place", None)
    if place and place.category:
        bump_pref(instance.itinerary.user, place.category, +3.0)