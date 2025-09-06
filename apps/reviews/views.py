from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Review
from .serializers import ReviewSerializer
from .permissions import IsAuthorOrAdminOrReadOnly

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['place']

    def get_permissions(self):
        if self.action in ['list','retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAuthorOrAdminOrReadOnly()]

    def get_queryset(self):
        qs = super().get_queryset()
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_approved=True)
        return qs