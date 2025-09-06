from django.contrib import admin
from .models import Post, Comment, Reaction

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "is_approved", "like_count", "comment_count", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("content", "user__email")

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "created_at")
    search_fields = ("content", "user__email")

@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "type", "created_at")
    list_filter = ("type",)
from django.contrib import admin

# Register your models here.
