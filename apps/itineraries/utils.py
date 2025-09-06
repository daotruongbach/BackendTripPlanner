from math import radians, sin, cos, sqrt, atan2
from django.conf import settings
import requests

GOONG_URL = getattr(settings, "GOONG_DISTANCE_URL", "https://rsapi.goong.io/DistanceMatrix")
GOONG_KEY = getattr(settings, "GOONG_API_KEY", "")

def haversine_m(lat1, lng1, lat2, lng2):
    if None in (lat1, lng1, lat2, lng2):
        return 0.0
    R = 6371000.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c  # meters

def estimate_leg(lat1, lng1, lat2, lng2, mode="walk"):
    """
    Trả về: {"distance_m": int, "duration_s": int, "cost_vnd": int, "mode": mode}
    - Ưu tiên Goong, fallback Haversine + tốc độ cấu hình.
    """
    profiles = settings.TRANSPORT_PROFILES
    prof = profiles.get(mode, profiles["walk"])

    distance_m, duration_s = 0, 0
    try:
        if GOONG_KEY:
            r = requests.get(GOONG_URL, params={
                "origins": f"{lat1},{lng1}",
                "destinations": f"{lat2},{lng2}",
                "vehicle": "car" if mode in ("taxi","bike") else "foot",
                "api_key": GOONG_KEY,
            }, timeout=6)
            r.raise_for_status()
            data = r.json()
            # goong format: rows[0].elements[0].distance.value, duration.value
            rows = data.get("rows", [])
            if rows and rows[0].get("elements"):
                el = rows[0]["elements"][0]
                distance_m = int(el.get("distance", {}).get("value", 0) or 0)
                duration_s = int(el.get("duration", {}).get("value", 0) or 0)
    except Exception:
        distance_m, duration_s = 0, 0

    # fallback nếu thiếu
    if distance_m <= 0:
        distance_m = int(haversine_m(lat1, lng1, lat2, lng2))
    if duration_s <= 0 and distance_m > 0:
        speed_ms = (prof["speed_kmh"] * 1000) / 3600.0
        duration_s = int(distance_m / speed_ms)

    # cost di chuyển
    per_km = distance_m / 1000.0
    cost_vnd = int(prof["base"] + prof["per_km"] * per_km)
    return {"distance_m": distance_m, "duration_s": duration_s, "cost_vnd": cost_vnd, "mode": mode}
