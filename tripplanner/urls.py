from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.urls import reverse_lazy

urlpatterns = [
    # Vào "/" tự chuyển sang admin
    path("", RedirectView.as_view(url=reverse_lazy("admin:index"), permanent=False), name="root-redirect"),

    path("admin/", admin.site.urls),

    # ==== AUTH (đúng theo bạn yêu cầu /api/auth/...) ====
    path("api/auth/", include("apps.accounts.urls")),   # <-- mới

    # Giữ tương thích cũ (nếu bạn còn gọi /api/accounts/...)
    path("api/accounts/", include("apps.accounts.urls")),

    # Các app khác
    path("api/places/", include("apps.places.urls")),
    path("api/reviews/", include("apps.reviews.urls")),
    path("api/itineraries/", include("apps.itineraries.urls")),
    path("api/", include("apps.posts.urls")),
]
