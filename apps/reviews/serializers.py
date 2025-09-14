from rest_framework import serializers
from .models import Review, ReviewStatus

class ReviewSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="get_status_display", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Review
        fields = ("id", "place", "rating", "comment", "status", "user_email", "created_at")
        read_only_fields = ("id", "status", "user_email", "created_at")

    def validate(self, attrs):
        # Không cho client tự set status
        if "status" in self.initial_data:
            raise serializers.ValidationError({"status": "Không được set trạng thái duyệt."})
        # Mỗi user 1 review/địa điểm
        request = self.context.get("request")
        if request and request.method == "POST":
            place = attrs.get("place")
            if place and Review.objects.filter(user=request.user, place=place).exists():
                raise serializers.ValidationError({"non_field_errors": ["Bạn đã đánh giá địa điểm này rồi."]})
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return Review.objects.create(user=request.user, status=ReviewStatus.PENDING, **validated_data)

class ReviewModerationSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=ReviewStatus.choices)

    class Meta:
        model = Review
        fields = ("status",)