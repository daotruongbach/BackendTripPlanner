from django.contrib import admin
from .models import Review, ReviewStatus

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "place", "user", "rating", "status", "created_at")
    list_filter = ("status", "rating", "place")
    search_fields = ("user__email", "place__name", "comment")
    autocomplete_fields = ("place",)