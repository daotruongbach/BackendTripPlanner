from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.urls import reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from apps.reco.views import PlaceRecommendView, MeStatsView

urlpatterns = [
    # "/" → admin
    path("", RedirectView.as_view(url=reverse_lazy("admin:index"), permanent=False), name="root-redirect"),

    path("admin/", admin.site.urls),

    # ==== AUTH (/api/auth/...) ====
    path("api/auth/", include("apps.accounts.urls")),

    # Giữ tương thích cũ (nếu còn gọi /api/accounts/...)
    path("api/accounts/", include("apps.accounts.urls")),

    # Các app khác
    path("api/places/", include("apps.places.urls")),
    path("api/reviews/", include("apps.reviews.urls")),
    path("api/itineraries/", include(("apps.itineraries.urls", "itineraries"), namespace="itineraries")),
    path("api/", include("apps.posts.urls")),   # router của posts

    path("api/reco/places/", PlaceRecommendView.as_view(), name="reco-places"),
    path("api/me/stats/", MeStatsView.as_view(), name="me-stats"),

]

# Phục vụ media/static ở môi trường dev
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()
