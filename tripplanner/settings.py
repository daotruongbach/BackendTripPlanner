from pathlib import Path
import os
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "dev-secret-change-me"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Bên thứ 3
    "rest_framework",
    "corsheaders",
    "django_filters",

    # App
    "apps.accounts",
    "apps.places",
    "apps.reviews",
    "apps.itineraries",
    "apps.posts",

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

DATABASES = {
  "default": {
    "ENGINE": "django.db.backends.mysql",
    "NAME": "csdl_tripplanner",
    "USER": "root",
    "PASSWORD": "1234",
    "HOST": "127.0.0.1",
    "PORT": "3306",
    "OPTIONS": {"charset":"utf8mb4"},
  }
}

AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 6,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True
# ... bên dưới TIME_ZONE, USE_TZ, v.v.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


STATIC_URL = "static/"

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]
CORS_ALLOW_CREDENTIALS = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "no-reply@tripplanner.local"

# === Goong === (theo yêu cầu: viết trực tiếp trong settings, không .env)
GOONG_API_KEY = "YfI57M128gfgDdjVFONP2Y8XQbqcv2Nqqv4mdMVe"
GOONG_DISTANCE_URL = "https://rsapi.goong.io/DistanceMatrix"

# === Ước tính chi phí vận chuyển (đơn vị VND & km/h) ===
TRANSPORT_PROFILES = {
    "taxi": {"base": 10000, "per_km": 14000, "speed_kmh": 25},
    "bike": {"base": 3000,  "per_km": 7000,  "speed_kmh": 22},
    "walk": {"base": 0,     "per_km": 0,     "speed_kmh": 4.5},
}