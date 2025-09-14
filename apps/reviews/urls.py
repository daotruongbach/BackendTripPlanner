from django.urls import path
from .views import ReviewListCreateView, ReviewDetailView, ReviewModerateView

urlpatterns = [
    path("", ReviewListCreateView.as_view()),                 # GET list, POST create
    path("<int:pk>/", ReviewDetailView.as_view()),            # GET detail, DELETE
    path("<int:pk>/moderate/", ReviewModerateView.as_view()), # POST approve/reject
]