# apps/posts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Post, Comment, Reaction

User = get_user_model()

class UserLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "username"]  # thêm full_name, avatar nếu có

class ReactionSerializer(serializers.ModelSerializer):
    user = UserLiteSerializer(read_only=True)

    class Meta:
        model = Reaction
        fields = ["id", "user", "type", "created_at"]

class CommentSerializer(serializers.ModelSerializer):
    user = UserLiteSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id", "post", "user", "content", "parent",
            "like_count", "created_at", "replies"
        ]
        read_only_fields = ["user", "like_count", "created_at", "replies"]

    def get_replies(self, obj):
        qs = obj.replies.select_related("user").order_by("created_at")
        return CommentSerializer(qs, many=True, context=self.context).data

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["user"] = request.user
        return super().create(validated_data)

class PostSerializer(serializers.ModelSerializer):
    user = UserLiteSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    liked_by_preview = serializers.SerializerMethodField()  # 3 người like gần nhất

    class Meta:
        model = Post
        fields = [
            "id", "user", "content", "image", "category",
            "place", "itinerary",
            "is_approved", "like_count", "comment_count",
            "created_at",
            "is_liked", "liked_by_preview",
        ]
        read_only_fields = [
            "user", "is_approved", "like_count", "comment_count",
            "created_at", "is_liked", "liked_by_preview",
        ]

    def get_is_liked(self, obj):
        req = self.context.get("request")
        if not req or not req.user or not req.user.is_authenticated:
            return False
        return Reaction.objects.filter(post=obj, user=req.user, type=Reaction.Type.LIKE).exists()

    def get_liked_by_preview(self, obj):
        qs = Reaction.objects.filter(post=obj, type=Reaction.Type.LIKE) \
                              .select_related("user").order_by("-created_at")[:3]
        return ReactionSerializer(qs, many=True).data

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["user"] = request.user
        return super().create(validated_data)