from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string

from apps.places.models import Place
from django.contrib.auth import get_user_model
User = get_user_model()

class Itinerary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="itineraries")
    name = models.CharField(max_length=255)
    is_public = models.BooleanField(default=False)

    # tổng thời gian DI CHUYỂN (giây) & tổng chi phí (vé + di chuyển)
    total_duration_s = models.PositiveIntegerField(default=0)
    total_cost = models.PositiveIntegerField(default=0)

    share_code = models.CharField(max_length=16, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def ensure_share_code(self):
        if not self.share_code:
            self.share_code = get_random_string(12)

    def __str__(self):
        return f"{self.name} ({self.user})"


class ItineraryItem(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name="items")
    place = models.ForeignKey(Place, on_delete=models.PROTECT)
    visit_start = models.DateTimeField()
    visit_end   = models.DateTimeField()
    transport_mode = models.CharField(max_length=16, default="walk")
    order = models.PositiveIntegerField(default=0, db_index=True)

    # === NEW: breakdown ===
    ticket_cost_vnd = models.PositiveIntegerField(default=0)    # vé của chính place này
    leg_distance_m  = models.PositiveIntegerField(default=0)    # quãng đường từ item trước -> item này
    leg_duration_s  = models.PositiveIntegerField(default=0)    # thời gian di chuyển của chặng
    leg_cost_vnd    = models.PositiveIntegerField(default=0)    # chi phí di chuyển của chặng

    class Meta:
        ordering = ("order", "id")

    def __str__(self):
        return f"{self.itinerary_id}#{self.order}: {self.place.name}"
