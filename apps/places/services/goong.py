import math
import requests
from django.conf import settings

# Haversine fallback (m -> s với tốc độ giả định)

def haversine_distance_m(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def goong_distance_matrix(origins, destinations, vehicle="car"):
    """
    origins/destinations: list[(lat, lng)]
    return: matrix distances (m) & durations (s)
    """
    try:
        origin_str = ";".join([f"{lat},{lng}" for lat, lng in origins])
        dest_str   = ";".join([f"{lat},{lng}" for lat, lng in destinations])
        params = {
            "origins": origin_str,
            "destinations": dest_str,
            "vehicle": vehicle,
            "api_key": settings.GOONG_API_KEY,
        }
        r = requests.get(settings.GOONG_DISTANCE_URL, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        # Chuẩn hoá về matrix [orig][dest] -> (dist_m, dur_s)
        rows = []
        for row in data.get('rows', []):
            cells = []
            for el in row.get('elements', []):
                dist = el.get('distance', {}).get('value', None)
                dur  = el.get('duration', {}).get('value', None)
                cells.append((dist, dur))
            rows.append(cells)
        if rows:
            return rows
    except Exception:
        pass
    # Fallback: haversine + tốc độ 25km/h (36*25=900 m/s) => 2.5 m/s? (thực tế 25km/h ≈ 6.94 m/s)
    rows = []
    speed_ms = 6.94
    for o_lat, o_lng in origins:
        line = []
        for d_lat, d_lng in destinations:
            d = haversine_distance_m(o_lat, o_lng, d_lat, d_lng)
            t = d / speed_ms
            line.append((int(d), int(t)))
        rows.append(line)
    return rows