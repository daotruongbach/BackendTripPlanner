from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Place
from .serializers import PlaceSerializer
from .filters import PlaceFilter
from .services.goong import goong_distance_matrix

class PlaceViewSet(mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   viewsets.GenericViewSet):
    queryset = Place.objects.all().order_by('-created_at')
    serializer_class = PlaceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PlaceFilter

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        lat = float(request.query_params.get('lat'))
        lng = float(request.query_params.get('lng'))
        radius = float(request.query_params.get('radius', 2000))  # mét
        category = request.query_params.get('category')
        qs = Place.objects.all()
        if category:
            qs = qs.filter(category__iexact=category)
        result = []
        for p in qs:
            if p.latitude is None or p.longitude is None:
                continue
            # quick filter bằng haversine đơn giản
            dist_m = 0
            try:
                from .services.goong import haversine_distance_m
                dist_m = haversine_distance_m(lat, lng, p.latitude, p.longitude)
            except Exception:
                pass
            if dist_m <= radius:
                result.append(p)
        ser = self.get_serializer(result, many=True)
        return Response({"count": len(result), "results": ser.data})