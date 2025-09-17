# apps/itineraries/views_auto_plan.py
from __future__ import annotations

import math
import requests
from datetime import date, datetime, timedelta
from typing import List, Tuple, Optional

from django.conf import settings
from django.db import transaction
from django.db.models import Sum

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.places.models import Place
from .models import Itinerary, ItineraryItem

# cố gắng import serializer chi tiết; nếu không có thì fallback
try:
    from .serializers import ItineraryDetailSerializer  # type: ignore
except Exception:  # pragma: no cover
    ItineraryDetailSerializer = None


# ==========================
# Helpers
# ==========================

def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _daterange(start_date: date, end_date: date) -> List[date]:
    days: List[date] = []
    d = start_date
    while d <= end_date:
        days.append(d)
        d += timedelta(days=1)
    return days


def _haversine_m(lat1, lon1, lat2, lon2) -> float:
    """Khoảng cách (m) theo haversine (fallback khi Goong lỗi)."""
    R = 6371000.0
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlmb = math.radians(float(lon2) - float(lon1))
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _goong_distance_duration_m_s(
    lat1: float, lon1: float, lat2: float, lon2: float, mode: str
) -> Tuple[int, int]:
    """
    Trả về (distance_m, duration_s). Ưu tiên gọi Goong; nếu thiếu key / lỗi -> fallback haversine + tốc độ.
    """
    mode = (mode or "walk").lower()
    key = getattr(settings, "GOONG_API_KEY", None)
    url = getattr(settings, "GOONG_DISTANCE_URL", None)

    # map mode theo Goong (foot, motorcycle, car)
    goong_mode = "foot"
    if mode in ("bike", "bicycle", "motorbike"):
        goong_mode = "motorcycle"
    elif mode in ("taxi", "car", "auto"):
        goong_mode = "car"

    if key and url:
        try:
            resp = requests.get(
                url,
                params={
                    "origins": f"{lat1},{lon1}",
                    "destinations": f"{lat2},{lon2}",
                    "vehicle": goong_mode,
                    "api_key": key,
                },
                timeout=6,
            )
            if resp.ok:
                js = resp.json()
                rows = js.get("rows") or []
                if rows and rows[0].get("elements"):
                    el = rows[0]["elements"][0]
                    dist = int(el.get("distance", {}).get("value") or 0)
                    dur = int(el.get("duration", {}).get("value") or 0)
                    if dist > 0 and dur > 0:
                        return dist, dur
        except Exception:
            pass  # fallback bên dưới

    # fallback: haversine + tốc độ từ TRANSPORT_PROFILES
    dist_m = _haversine_m(lat1, lon1, lat2, lon2)
    profiles = getattr(settings, "TRANSPORT_PROFILES", {})
    speed_kmh = float(profiles.get(mode, {}).get("speed_kmh", 4.5))
    dur_s = int((dist_m / 1000.0) / max(speed_kmh, 0.1) * 3600.0)
    return int(dist_m), max(1, dur_s)


def _estimate_cost(mode: str, distance_m: float) -> int:
    """Tính chi phí di chuyển theo profiles trong settings."""
    profiles = getattr(settings, "TRANSPORT_PROFILES", {})
    prof = profiles.get((mode or "walk").lower(), {"base": 0, "per_km": 0})
    base = int(prof.get("base", 0))
    per_km = int(prof.get("per_km", 0))
    km = float(distance_m or 0) / 1000.0
    return int(base + per_km * km)


def _ticket_price_of(place: Place) -> int:
    """Lấy giá vé an toàn (hỗ trợ nhiều tên cột)."""
    return int(
        getattr(place, "ticket_price", None)
        or getattr(place, "ticket_price_vnd", None)
        or 0
    )


def _frontload_split(total: int, n_days: int) -> List[int]:
    """Chia front-load: ngày đầu nhận nhiều hơn nếu không chia hết."""
    if n_days <= 0:
        return []
    base = total // n_days
    rem = total % n_days
    return [base + (1 if i < rem else 0) for i in range(n_days)]


def _nearest_neighbor_order(start_lat: float, start_lng: float, places: List[Place]) -> List[Place]:
    """Sắp xếp greedy theo điểm gần nhất tiếp theo, bắt đầu từ (start_lat,lng)."""
    remaining = places[:]
    ordered: List[Place] = []
    cur_lat, cur_lng = start_lat, start_lng

    while remaining:
        best = None
        best_d = 10 ** 12
        for p in remaining:
            try:
                d = _haversine_m(cur_lat, cur_lng, float(p.latitude), float(p.longitude))
            except Exception:
                d = 10 ** 12
            if d < best_d:
                best_d = d
                best = p
        ordered.append(best)
        cur_lat, cur_lng = float(best.latitude), float(best.longitude)
        remaining.remove(best)
    return ordered


def _serialize_itinerary(itin: Itinerary) -> dict:
    """Fallback serializer nếu không có ItineraryDetailSerializer."""
    items = (
        ItineraryItem.objects.filter(itinerary=itin)
        .select_related("place")
        .order_by("visit_date", "order", "id")
    )
    items_detail = []
    cost_breakdown = []
    transport_breakdown = []
    last_per_day: dict = {}

    for it in items:
        items_detail.append(
            {
                "id": it.id,
                "place": it.place_id,
                "place_name": getattr(it.place, "name", ""),
                "visit_date": it.visit_date.isoformat() if it.visit_date else None,
                "transport_mode": it.transport_mode,
                "order": it.order,
                "ticket_cost_vnd": it.ticket_cost_vnd,
                "leg_distance_m": it.leg_distance_m,
                "leg_duration_s": it.leg_duration_s,
                "leg_cost_vnd": it.leg_cost_vnd,
            }
        )
        cost_breakdown.append(
            {
                "place_id": it.place_id,
                "place_name": getattr(it.place, "name", ""),
                "visit_date": it.visit_date.isoformat() if it.visit_date else None,
                "ticket_cost_vnd": it.ticket_cost_vnd,
            }
        )
        # transport breakdown theo cặp trong cùng ngày
        day = it.visit_date.isoformat() if it.visit_date else ""
        if day not in last_per_day:
            last_per_day[day] = it
        else:
            prev = last_per_day[day]
            if prev and it.leg_distance_m:
                transport_breakdown.append(
                    {
                        "date": day,
                        "from_place_id": prev.place_id,
                        "from_place_name": getattr(prev.place, "name", ""),
                        "to_place_id": it.place_id,
                        "to_place_name": getattr(it.place, "name", ""),
                        "mode": it.transport_mode,
                        "distance_km": round(float(it.leg_distance_m) / 1000.0, 3),
                        "duration_min": round(float(it.leg_duration_s) / 60.0, 1),
                        "leg_cost_vnd": it.leg_cost_vnd,
                    }
                )
            last_per_day[day] = it

    ticket_total = sum(x["ticket_cost_vnd"] for x in items_detail)
    transport_total = sum(x["leg_cost_vnd"] for x in items_detail)

    return {
        "id": itin.id,
        "name": itin.name,
        "is_public": itin.is_public,
        "total_cost": itin.total_cost,
        "total_duration_s": itin.total_duration_s,
        "share_code": itin.share_code,
        "items_detail": items_detail,
        "cost_breakdown": cost_breakdown,
        "transport_breakdown": transport_breakdown,
        "summary": {
            "ticket_total_vnd": ticket_total,
            "transport_total_vnd": transport_total,
            "travel_duration_min": round(float(itin.total_duration_s) / 60.0, 1),
        },
    }


# ==========================
# API
# ==========================

class AutoPlanFromRecoView(APIView):
    """
    POST /api/itineraries/auto-plan/
    Body:
    {
      "start_date": "YYYY-MM-DD",
      "end_date":   "YYYY-MM-DD",
      "n_places":   6,
      "lat": 10.78,
      "lng": 106.7,
      "transport_mode": "bike",    // "walk" | "bike" | "taxi"
      "name": "Lịch trình...",
      "exclude_cats": ["FOOD","DRINK"],
      "limit": 60
    }
    """

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=401)

        data = request.data or {}
        try:
            start_date = _parse_date(str(data.get("start_date")))
            end_date = _parse_date(str(data.get("end_date")))
        except Exception:
            return Response({"detail": "start_date/end_date phải là YYYY-MM-DD"}, status=400)

        if end_date < start_date:
            return Response({"detail": "end_date phải >= start_date"}, status=400)

        try:
            n_places = int(data.get("n_places") or 0)
        except Exception:
            n_places = 0
        if n_places <= 0:
            return Response({"detail": "n_places phải > 0"}, status=400)

        # toạ độ xuất phát (tùy chọn)
        lat = data.get("lat")
        lng = data.get("lng")
        try:
            lat = float(lat) if lat is not None else None
            lng = float(lng) if lng is not None else None
        except Exception:
            lat, lng = None, None

        transport_mode = (data.get("transport_mode") or "walk").lower()
        name = data.get("name") or "Lịch trình tự động từ gợi ý"
        exclude_cats = data.get("exclude_cats") or []
        limit = int(data.get("limit") or 60)

        # 1) Lấy danh sách Place ứng viên
        qs = Place.objects.all()
        if exclude_cats:
            qs = qs.exclude(category__in=exclude_cats)
        qs = qs.exclude(latitude__isnull=True).exclude(longitude__isnull=True)

        # Nếu có toạ độ xuất phát -> ưu tiên theo khoảng cách
        if lat is not None and lng is not None:
            candidates = list(qs[:limit * 3])  # lấy rộng hơn để sort tại RAM
            candidates.sort(
                key=lambda p: _haversine_m(lat, lng, float(p.latitude), float(p.longitude))
            )
        else:
            candidates = list(qs.order_by("-id")[:limit * 3])

        candidates = candidates[:max(n_places, 1)]  # đủ số lượng yêu cầu

        # 2) Chia theo ngày kiểu front-load
        days = _daterange(start_date, end_date)
        share = _frontload_split(len(candidates), len(days))

        # 3) Sắp thứ tự trong từng ngày theo nearest-neighbor
        plan_by_day: List[Tuple[date, List[Place]]] = []
        idx = 0
        for i, d in enumerate(days):
            take = share[i] if i < len(share) else 0
            group = candidates[idx: idx + take]
            idx += take
            if group:
                if lat is not None and lng is not None:
                    ordered = _nearest_neighbor_order(lat, lng, group)
                else:
                    ordered = group
                plan_by_day.append((d, ordered))

        if not plan_by_day:
            return Response({"detail": "Không đủ địa điểm để tạo lịch trình."}, status=400)

        # 4) Tạo Itinerary & Items + tính vé/di chuyển
        with transaction.atomic():
            itin = Itinerary.objects.create(
                user=request.user,
                name=name,
                is_public=False,
            )

            running_order = 0
            for d, group_places in plan_by_day:
                prev: Optional[ItineraryItem] = None
                for p in group_places:
                    running_order += 1

                    # vé
                    ticket_vnd = _ticket_price_of(p)

                    leg_distance_m = 0
                    leg_duration_s = 0
                    leg_cost_vnd = 0

                    if prev is not None:
                        # đoạn di chuyển từ điểm trước -> điểm hiện tại
                        leg_distance_m, leg_duration_s = _goong_distance_duration_m_s(
                            float(prev.place.latitude),
                            float(prev.place.longitude),
                            float(p.latitude),
                            float(p.longitude),
                            transport_mode,
                        )
                        leg_cost_vnd = _estimate_cost(transport_mode, leg_distance_m)

                    item = ItineraryItem.objects.create(
                        itinerary=itin,
                        place=p,
                        visit_date=d,
                        transport_mode=transport_mode,
                        order=running_order,
                        ticket_cost_vnd=int(ticket_vnd or 0),
                        leg_distance_m=int(leg_distance_m or 0),
                        leg_duration_s=int(leg_duration_s or 0),
                        leg_cost_vnd=int(leg_cost_vnd or 0),
                    )
                    prev = item

            # 5) Recalc tổng trên itinerary
            agg = ItineraryItem.objects.filter(itinerary=itin).aggregate(
                ticket_total=Sum("ticket_cost_vnd"),
                transport_total=Sum("leg_cost_vnd"),
                travel_s=Sum("leg_duration_s"),
            )
            itin.total_cost = int(agg.get("ticket_total") or 0) + int(agg.get("transport_total") or 0)
            itin.total_duration_s = int(agg.get("travel_s") or 0)

            # nếu có ensure_share_code trong model thì gọi, không có cũng không sao
            try:
                itin.ensure_share_code()  # type: ignore
            except Exception:
                pass

            itin.save(update_fields=["total_cost", "total_duration_s", "share_code"])

        # 6) Response
        if ItineraryDetailSerializer:
            return Response(ItineraryDetailSerializer(itin).data, status=status.HTTP_201_CREATED)
        return Response(_serialize_itinerary(itin), status=status.HTTP_201_CREATED)
