from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "place", "user", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("place__name", "user__email", "comment")
