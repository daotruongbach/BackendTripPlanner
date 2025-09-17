from pathlib import Path
from datetime import timedelta
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ===== Core =====
SECRET_KEY = "dev-secret-change-me"
DEBUG = True
ALLOWED_HOSTS = ["*"]

# ===== Apps =====
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # 3rd-party
    "rest_framework",
    "corsheaders",
    "django_filters",

    # Local apps
    "apps.accounts",
    "apps.places",
    "apps.reviews.apps.ReviewsConfig",
    "apps.itineraries",
    "apps.posts",
    "apps.reco",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tripplanner.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "tripplanner.wsgi.application"

# ===== Database (MySQL dev) =====
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "csdl_tripplanner",
        "USER": "root",
        "PASSWORD": "1234",          # <-- đổi theo máy bạn
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

# ===== Auth =====
AUTH_USER_MODEL = "accounts.User"

# ===== DRF & JWT =====
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 6,
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ===== I18N / TZ =====
LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ===== Static & Media =====
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ===== CORS =====
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
]
CORS_ALLOW_CREDENTIALS = True

# ===== Email dev =====
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "no-reply@tripplanner.local"

# ===== Goong (distance) =====
GOONG_API_KEY = "YfI57M128gfgDdjVFONP2Y8XQbqcv2Nqqv4mdMVe"
GOONG_DISTANCE_URL = "https://rsapi.goong.io/DistanceMatrix"

# ===== Transport profiles (ước tính chi phí) =====
TRANSPORT_PROFILES = {
    "taxi": {"base": 10000, "per_km": 14000, "speed_kmh": 25},
    "bike": {"base": 3000,  "per_km": 7000,  "speed_kmh": 22},
    "walk": {"base": 0,     "per_km": 0,     "speed_kmh": 4.5},
}

# ===== Recommendation (gợi ý địa điểm) =====
RECO_WEIGHTS = {"w_cat": 2.0, "w_rate": 1.0, "w_dist": -0.3, "w_weather": 1.0}
RECO_ALWAYS_EXCLUDE = ["FOOD", "DRINK"]

# ===== OpenWeather =====
OPENWEATHER_API_KEY = "6230587d2afe770f5549313b4465cf9c"

# ===== Cache local =====
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "tripplanner-local-cache",
    }
}

# ===== VNPay (Sandbox) — KHÔNG dùng .env =====
VNPAY_VERSION      = "2.1.0"
VNPAY_TMN_CODE     = "F73OB93A"  # từ email sandbox
VNPAY_HASH_SECRET  = "7Y1CE4O2JSU7NVUSLJEVXJUS5I5T0JPW"  # từ email sandbox
VNPAY_PAYMENT_URL  = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
VNPAY_RETURN_URL = "http://127.0.0.1:8000/api/itineraries/payments/vnpay/return/"
VNPAY_IPN_URL    = "http://127.0.0.1:8000/api/itineraries/payments/vnpay/ipn/"
