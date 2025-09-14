# apps/posts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, CommentViewSet

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="posts")
router.register(r"comments", CommentViewSet, basename="comments")  # cho các action like/reply xoay quanh comment id

urlpatterns = [
    path("", include(router.urls)),
]