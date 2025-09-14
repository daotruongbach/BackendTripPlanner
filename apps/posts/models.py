# apps/posts/models.py
from django.db import models
from django.contrib.auth import get_user_model
from apps.places.models import Place
from apps.itineraries.models import Itinerary

User = get_user_model()

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to="posts/", null=True, blank=True)
    category = models.CharField(max_length=50, null=False, blank=False)

    # ngữ cảnh tuỳ chọn
    place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")
    itinerary = models.ForeignKey(Itinerary, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")

    # counters & moderation
    is_approved = models.BooleanField(default=True)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["is_approved"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"Post#{self.pk} by {self.user_id}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies")

    like_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["post", "created_at"]) ]

    def __str__(self):
        return f"Comment#{self.pk} on Post#{self.post_id}"


class Reaction(models.Model):
    class Type(models.TextChoices):
        LIKE = "LIKE", "Like"
        # sau này có thể mở rộng: LOVE, HAHA, WOW...

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reactions")
    type = models.CharField(max_length=8, choices=Type.choices, default=Type.LIKE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user")  # 1 user 1 reaction / post
        indexes = [
            models.Index(fields=["post", "user"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"Reaction({self.type}) post={self.post_id} user={self.user_id}"


class CommentLike(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comment_likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("comment", "user")
        indexes = [
            models.Index(fields=["comment", "user"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"CommentLike comment={self.comment_id} user={self.user_id}"