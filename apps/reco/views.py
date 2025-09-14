# apps/reco/views.py
from django.conf import settings
from django.db.models import Count, Max
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.places.models import Place
from apps.itineraries.models import ItineraryItem
from apps.posts.models import Reaction  # dùng Reaction để lấy like theo user
from .serializers import PlaceBriefSerializer
from .services.weather import hourly_like_for
from .services.scoring import place_score_basic


def _coords_of(place):
    lat = getattr(place, "latitude", None) or getattr(place, "lat", None)
    lon = getattr(place, "longitude", None) or getattr(place, "lng", None) or getattr(place, "lon", None)
    try:
        return float(lat), float(lon)
    except Exception:
        return None, None


def _parse_cats_list(value):
    if not value:
        return []
    return [c.strip().upper() for c in value.split(",") if c.strip()]


class PlaceRecommendView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        lat = request.GET.get("lat")
        lng = request.GET.get("lng")
        limit = max(1, min(int(request.GET.get("limit", 20)), 100))
        only_top_cats = request.GET.get("top_cats", "1") == "1"
        include_score = request.GET.get("include_score", "0") == "1"

        # 1) like_pref = số LIKE theo category của user (Reaction.type = LIKE)
        like_pref_qs = (
            Reaction.objects.filter(user=user, type=Reaction.Type.LIKE, post__category__isnull=False)
            .values("post__category")
            .annotate(c=Count("id"))
        )
        like_pref = {row["post__category"]: row["c"] for row in like_pref_qs}

        # 2) Loại các nơi đã đi
        visited_ids = set(
            ItineraryItem.objects.filter(itinerary__user=user).values_list("place_id", flat=True)
        )

        # 3) Base queryset + exclude cố định và theo param
        qs = Place.objects.exclude(id__in=visited_ids)
        excluded = set(getattr(settings, "RECO_ALWAYS_EXCLUDE", []))
        excluded |= set(_parse_cats_list(request.GET.get("exclude_cats")))
        if excluded:
            qs = qs.exclude(category__in=list(excluded))

        # 4) only_top_cats: lọc top 5 category user hay like nhất
        if only_top_cats and like_pref:
            top_cats = sorted(like_pref.items(), key=lambda kv: kv[1], reverse=True)
            top_cats = [k for k, _ in top_cats[:5]]
            qs = qs.filter(category__in=top_cats)

        # 5) Thời tiết theo toạ độ (nếu có)
        hourly = None
        try:
            if lat and lng:
                lat = float(lat)
                lng = float(lng)
                hourly = hourly_like_for(lat, lng)
        except Exception:
            hourly = None

        # 6) Haversine (dự phòng nếu utils không có)
        try:
            from apps.itineraries.utils import haversine_m
        except Exception:
            from math import radians, sin, cos, asin, sqrt

            def haversine_m(lat1, lon1, lat2, lon2):
                R = 6371000.0
                dlat = radians(lat2 - lat1)
                dlon = radians(lon2 - lon1)
                a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
                return 2 * R * asin(sqrt(a))

        candidates = list(qs[:1000])

        # 7) Tính điểm cơ bản cho từng place
        scored = []
        for p in candidates:
            km = None
            if lat and lng:
                plat, plon = _coords_of(p)
                if plat is not None and plon is not None:
                    km = haversine_m(lat, lng, plat, plon) / 1000.0
            s = place_score_basic(p.category, km=km, hourly_forecast=hourly, like_pref=like_pref)
            scored.append((s, p, km))

        # tie-break: score ↓, distance ↑, id ↑
        scored.sort(key=lambda t: (-float(t[0]), (t[2] if t[2] is not None else 1e9), t[1].id))

        # 8) Serialize kết quả
        results = []
        for idx, (s, p, km) in enumerate(scored[:limit], start=1):
            item = PlaceBriefSerializer(p).data
            if include_score:
                item.update({"rank": idx, "score": round(float(s), 3)})
            results.append(item)

        return Response({"count": len(scored), "results": results})


class MeStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        last = (
            ItineraryItem.objects.filter(itinerary__user=request.user, visit_date__isnull=False)
            .aggregate(Max("visit_date"))["visit_date__max"]
        )
        days = (timezone.localdate() - last).days if last else None
        return Response({"last_trip_date": last, "days_since_last_trip": days})
