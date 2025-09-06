from django.contrib import admin
from .models import Place

@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "ticket_price", "rating_avg", "reviews_count", "created_at")
    search_fields = ("name", "address", "description")
    list_filter = ("category",)
    ordering = ("name",)
