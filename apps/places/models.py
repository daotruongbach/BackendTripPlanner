from django.db import models

class Place(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    # không dùng choices để nhận mọi phân loại bạn ghi trong file
    category = models.CharField(max_length=64, db_index=True)
    address = models.CharField(max_length=255, blank=True)

    latitude  = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # giờ/giá dạng TEXT tuỳ ý
    open_time    = models.CharField(max_length=50, blank=True, null=True)
    close_time   = models.CharField(max_length=50, blank=True, null=True)
    ticket_price = models.PositiveIntegerField(null=True, blank=True, db_index=True)

    website = models.CharField(max_length=255, blank=True,null=True)
    phone   = models.CharField(max_length=50, blank=True,null=True)

    rating_avg    = models.FloatField(default=0,null=True)
    reviews_count = models.PositiveIntegerField(default=0,null=True)
    created_at    = models.DateTimeField(auto_now_add=True,null=True)

    # ==== Cloudinary ====
    image_url = models.URLField(max_length=512, blank=True, null=True)  # để render
    image_public_id = models.CharField(max_length=255, blank=True, null=True)  # để quản lý/xoá

    class Meta:
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name
