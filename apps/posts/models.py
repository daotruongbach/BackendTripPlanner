from django.db import models
from django.contrib.auth import get_user_model
from apps.places.models import Place
from apps.itineraries.models import Itinerary

User = get_user_model()

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(blank=True)
    image_url = models.URLField(max_length=512, blank=True, null=True)

    # gắn ngữ cảnh (tuỳ chọn)
    place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")
    itinerary = models.ForeignKey(Itinerary, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")

    is_approved = models.BooleanField(default=True)  # nếu muốn duyệt tay: để False
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["is_approved"]),
        ]

    def __str__(self):
        return f"Post#{self.pk} by {self.user}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)


class Reaction(models.Model):
    class Type(models.TextChoices):
        LIKE = "LIKE", "Like"
        LOVE = "LOVE", "Love"
        WOW = "WOW", "Wow"

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reactions")
    type = models.CharField(max_length=8, choices=Type.choices, default=Type.LIKE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("post", "user"),)  # mỗi user 1 reaction cho 1 post
from django.db import models

# Create your models here.
