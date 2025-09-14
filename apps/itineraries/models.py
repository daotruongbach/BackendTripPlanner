# apps/itineraries/models.py
from django.db import models
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model
from apps.places.models import Place

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

    # === NEW: chỉ lưu NGÀY tham quan ===
    visit_date = models.DateField(null=True, blank=True, db_index=True)

    transport_mode = models.CharField(max_length=16, default="walk")
    order = models.PositiveIntegerField(default=0, db_index=True)

    # breakdown
    ticket_cost_vnd = models.PositiveIntegerField(default=0)
    leg_distance_m  = models.PositiveIntegerField(default=0)
    leg_duration_s  = models.PositiveIntegerField(default=0)
    leg_cost_vnd    = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("visit_date", "order", "id")  # nhóm theo ngày, rồi thứ tự trong ngày

    def __str__(self):
        return f"{self.itinerary_id}#{self.order}: {self.place.name}"
