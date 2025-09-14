from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Review, ReviewStatus
from .serializers import ReviewSerializer, ReviewModerationSerializer
from .permissions import IsOwnerOrStaffCanDelete
from apps.accounts.permissions import MinRole
from apps.accounts.models import Role
from rest_framework.exceptions import ValidationError

class ReviewListCreateView(generics.ListCreateAPIView):
    """
    GET:
      - User thường: chỉ thấy APPROVED
      - Staff/Admin: ?all=1 để xem tất cả, hoặc ?status=pending/approved/rejected
    POST:
      - Tạo review mới -> status=PENDING
    """
    serializer_class = ReviewSerializer

    def get_queryset(self):
        qs = Review.objects.select_related("user", "place")
        u = self.request.user
        status_param = self.request.query_params.get("status")
        see_all = self.request.query_params.get("all") in ("1", "true", "yes")

        if u.is_authenticated and u.has_role_at_least(Role.STAFF):
            if status_param in ("pending", "approved", "rejected"):
                map2val = {
                    "pending": ReviewStatus.PENDING,
                    "approved": ReviewStatus.APPROVED,
                    "rejected": ReviewStatus.REJECTED,
                }
                return qs.filter(status=map2val[status_param])
            return qs if see_all else qs.filter(status=ReviewStatus.APPROVED)
        return qs.filter(status=ReviewStatus.APPROVED)

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            # fallback (khi race condition)
            raise ValidationError({"non_field_errors": ["Bạn đã đánh giá địa điểm này rồi."]})

class ReviewDetailView(generics.RetrieveDestroyAPIView):
    queryset = Review.objects.select_related("user", "place")
    serializer_class = ReviewSerializer
    permission_classes = [IsOwnerOrStaffCanDelete]

    def perform_destroy(self, instance):
        place = instance.place
        instance.delete()
        Review.recalc_place_stats(place)

class ReviewModerateView(APIView):
    """POST /api/reviews/<id>/moderate/  body: {"status": 2|3} """
    permission_classes = [permissions.IsAuthenticated, MinRole.at_least(Role.STAFF)]

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        old = review.status
        s = ReviewModerationSerializer(review, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        if (old != ReviewStatus.APPROVED) or (review.status != old):
            Review.recalc_place_stats(review.place)
        return Response(ReviewSerializer(review).data, status=status.HTTP_200_OK)