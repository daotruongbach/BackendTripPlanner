# apps/itineraries/services/transport.py
from __future__ import annotations
import math
import requests
from dataclasses import dataclass
from typing import Tuple
from django.conf import settings

# Map our modes → Goong vehicle value
_GOONG_VEHICLE = {
    "taxi": "car",
    "bike": "motorcycle",
    "walk": "foot",  # goong may alias to walking; fallback handled below
}

@dataclass
class Leg:
    distance_m: int
    duration_s: int
    cost_vnd: int


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Simple fallback (meters)."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi/2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _estimate_duration(distance_m: float, mode: str) -> int:
    prof = settings.TRANSPORT_PROFILES.get(mode, settings.TRANSPORT_PROFILES.get("walk", {}))
    speed_kmh = float(prof.get("speed_kmh", 4.5))
    hours = (distance_m / 1000.0) / max(speed_kmh, 0.1)
    return int(hours * 3600)


def _estimate_cost(distance_m: float, mode: str) -> int:
    prof = settings.TRANSPORT_PROFILES.get(mode, settings.TRANSPORT_PROFILES.get("walk", {}))
    base = float(prof.get("base", 0))
    per_km = float(prof.get("per_km", 0))
    return int(round(base + per_km * (distance_m / 1000.0)))


def goong_distance_duration(lat1: float, lng1: float, lat2: float, lng2: float, mode: str) -> Tuple[int, int]:
    """
    Call Goong Distance Matrix. If request fails, return haversine + estimated duration.
    """
    try:
        vehicle = _GOONG_VEHICLE.get(mode, "car")
        resp = requests.get(
            settings.GOONG_DISTANCE_URL,
            params={
                "origins": f"{lat1},{lng1}",
                "destinations": f"{lat2},{lng2}",
                "vehicle": vehicle,
                "api_key": settings.GOONG_API_KEY,
            },
            timeout=8,
        )
        data = resp.json()
        # Goong returns a Google-like schema
        row0 = data["rows"][0]
        el0 = row0["elements"][0]
        dist_m = int(el0["distance"]["value"])  # meters
        dur_s = int(el0["duration"]["value"])   # seconds
        return dist_m, dur_s
    except Exception:
        # Fallback: haversine + speed profile
        d = _haversine_m(lat1, lng1, lat2, lng2)
        return int(d), _estimate_duration(d, mode)


def build_leg(lat1: float, lng1: float, lat2: float, lng2: float, mode: str) -> Leg:
    dist_m, dur_s = goong_distance_duration(lat1, lng1, lat2, lng2, mode)
    cost = _estimate_cost(dist_m, mode)
    return Leg(distance_m=int(dist_m), duration_s=int(dur_s), cost_vnd=int(cost))