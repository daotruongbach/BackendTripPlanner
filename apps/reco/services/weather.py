import requests
from django.core.cache import cache
from django.conf import settings

def _cache_get_or_fetch(key, minutes, fn):
    data = cache.get(key)
    if data is not None:
        return data
    try:
        data = fn()
    except Exception:
        # Lỗi mạng/API → trả rỗng để hệ thống vẫn chạy
        return {"list": []}
    cache.set(key, data, timeout=minutes*60)
    return data

def forecast3h(lat, lon):
    key = getattr(settings, "OPENWEATHER_API_KEY", None)
    if not key:
        return {"list": []}
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"lat": lat, "lon": lon, "appid": key, "units": "metric", "lang": "vi"}
    cache_key = f"owm:fc3h:{round(float(lat),3)}:{round(float(lon),3)}"
    def _fetch():
        r = requests.get(url, params=params, timeout=7)
        r.raise_for_status()
        return r.json()
    return _cache_get_or_fetch(cache_key, 15, _fetch)

def pick_nearest_slot(fc_json, target_ts=None):
    lst = (fc_json or {}).get("list") or []
    if not lst:
        return None
    item = lst[0] if not target_ts else min(lst, key=lambda it: abs((it.get("dt") or 0) - target_ts))
    main = item.get("main") or {}
    clouds = (item.get("clouds") or {}).get("all", 0)
    return {
        "dt": item.get("dt"),
        "pop": float(item.get("pop") or 0.0),
        "temp": float(main.get("temp") or 0.0),
        # Free plan không có UVI; ước lượng thô từ độ mây để khỏi văng lỗi
        "uvi": max(0.0, 10.0 * (1.0 - float(clouds)/100.0)),
        "clouds": clouds,
        "rain_3h": (item.get("rain") or {}).get("3h"),
    }

def hourly_like_for(lat, lon, target_ts=None):
    return pick_nearest_slot(forecast3h(lat, lon), target_ts=target_ts)
