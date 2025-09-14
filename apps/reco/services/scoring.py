from django.conf import settings
import math
from ..category_traits import CATEGORY_TRAITS

DEFAULT_WEIGHTS = {"w_cat": 2.0, "w_dist": -0.3, "w_weather": 1.0}  # bỏ w_rate cho bản cơ bản
def _W(): return getattr(settings, "RECO_WEIGHTS", DEFAULT_WEIGHTS)

def weather_penalty(category, hourly_forecast):
    if not hourly_forecast: return 0.0
    t = CATEGORY_TRAITS.get(category or "", {})
    pop = float(hourly_forecast.get("pop", 0) or 0)
    uvi = float(hourly_forecast.get("uvi", 0) or 0)
    temp = float(hourly_forecast.get("temp", 0) or 0)
    pen = 0.0
    if t.get("outdoor"):
        if pop >= 0.5: pen -= 2.0
        if uvi >= 8:   pen -= 1.0
        if temp >= 34: pen -= 0.5
    if t.get("indoor"):
        if pop >= 0.5: pen += 1.0
    return pen

def pref_from_likes(category, like_pref):

    if not like_pref: return 0.0
    c = like_pref.get(category or "", 0)
    return math.log1p(float(c))

def place_score_basic(category, km=None, hourly_forecast=None, like_pref=None):
    w = _W(); s = 0.0
    s += w["w_cat"] * pref_from_likes(category, like_pref)
    if km is not None: s += w["w_dist"] * km
    s += w["w_weather"] * weather_penalty(category, hourly_forecast)
    return s
