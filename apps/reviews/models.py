# apps/reviews/models.py
from django.db import models
from django.conf import settings
from django.db.models import Avg, Count

User = settings.AUTH_USER_MODEL

class ReviewStatus(models.IntegerChoices):
    PENDING  = 1, "Chờ duyệt"
    APPROVED = 2, "Đã duyệt"
    REJECTED = 3, "Từ chối"

class Review(models.Model):
    user    = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    place   = models.ForeignKey("places.Place", on_delete=models.CASCADE, related_name="reviews")
    rating  = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    status  = models.PositiveSmallIntegerField(choices=ReviewStatus.choices, default=ReviewStatus.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("user", "place")]  # mỗi user 1 review/địa điểm (bỏ nếu muốn)

    @staticmethod
    def recalc_place_stats(place):
        """Cập nhật Place.rating_avg / Place.reviews_count dựa trên review đã APPROVED."""
        qs  = place.reviews.filter(status=ReviewStatus.APPROVED)
        agg = qs.aggregate(avg=Avg("rating"), cnt=Count("id"))
        avg, cnt = agg["avg"], agg["cnt"]

        # Nếu không có review approved → để NULL (đừng set 0)
        fields = []
        if hasattr(place, "rating_avg"):
            place.rating_avg = round(float(avg), 1) if cnt else None
            fields.append("rating_avg")
        if hasattr(place, "reviews_count"):
            place.reviews_count = int(cnt) if cnt else None
            fields.append("reviews_count")
        if fields:
            place.save(update_fields=fields)
