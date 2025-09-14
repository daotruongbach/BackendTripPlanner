from django.utils import timezone
from ..models import UserCategoryPreference
MIN_SCORE, MAX_SCORE = -10.0, 10.0

def bump_pref(user, category, delta):
    if not category: return
    pref, _ = UserCategoryPreference.objects.get_or_create(user=user, category=category)
    pref.score = max(MIN_SCORE, min(MAX_SCORE, pref.score + float(delta)))
    pref.last_event_at = timezone.now()
    pref.save(update_fields=["score", "last_event_at"])