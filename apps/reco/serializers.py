from rest_framework import serializers
from apps.places.models import Place
class PlaceBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ["id", "name", "category", "rating_avg", "image_url", "latitude", "longitude"]