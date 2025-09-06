from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Itinerary, ItineraryItem
from .serializers import ItinerarySerializer
from apps.places.models import Place

class ItineraryViewSet(viewsets.ModelViewSet):
    serializer_class = ItinerarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Itinerary.objects.filter(Q(user=user) | Q(is_public=True))

    @action(detail=True, methods=['get'])
    def suggestions(self, request, pk=None):
        # Gợi ý FOOD/HOTEL/EVENT gần điểm đầu/cuối trong lịch trình
        it = self.get_object()
        items = list(it.items.all().select_related('place'))
        if not items:
            return Response({"results": []})
        seed = items[-1].place
        lat, lng = seed.latitude, seed.longitude
        radius_m = int(request.query_params.get('radius', 1500))
        cats = request.query_params.get('categories', 'FOOD,HOTEL,EVENT').split(',')
        qs = Place.objects.filter(category__in=cats)
        res = []
        from apps.places.services.goong import haversine_distance_m
        for p in qs:
            if p.latitude is None:
                continue
            d = haversine_distance_m(lat, lng, p.latitude, p.longitude)
            if d <= radius_m:
                res.append({
                    'id': p.id,
                    'name': p.name,
                    'category': p.category,
                    'address': p.address,
                    'distance_m': int(d),
                    'rating_avg': p.rating_avg,
                    'image_url': p.image_url,
                })
        res.sort(key=lambda x: (x['distance_m'], -float(x['rating_avg'] or 0)))
        return Response({"count": len(res), "results": res[:20]})
