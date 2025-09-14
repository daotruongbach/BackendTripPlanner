# apps/posts/admin.py
from django.contrib import admin
from .models import Post, Comment, Reaction, CommentLike

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "category", "like_count", "comment_count", "is_approved", "created_at")
    list_filter = ("is_approved", "category")
    search_fields = ("content", "user__email")

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "like_count", "created_at")
    search_fields = ("content", "user__email")

@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "type", "created_at")
    list_filter = ("type",)
    search_fields = ("user__email",)

@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ("id", "comment", "user", "created_at")
    search_fields = ("comment__content", "user__email")