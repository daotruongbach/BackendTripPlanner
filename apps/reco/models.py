from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class UserCategoryPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="category_prefs")
    category = models.CharField(max_length=64, db_index=True)
    score = models.FloatField(default=0.0)           # [-10..+10]
    last_event_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = (("user", "category"),)
        indexes = [models.Index(fields=["user", "category"])]

class UserPlaceStat(models.Model):  # tuỳ chọn
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    place = models.ForeignKey("places.Place", on_delete=models.CASCADE)
    visited_count = models.PositiveIntegerField(default=0)
    last_visit_date = models.DateField(null=True, blank=True)
    class Meta:
        unique_together = (("user", "place"),)
        indexes = [models.Index(fields=["user", "place"])]