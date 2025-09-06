from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Post, Comment, Reaction

User = get_user_model()

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]

class CommentSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "user", "content", "created_at"]

class PostSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    my_reaction = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id", "user", "content", "image_url",
            "place", "itinerary",
            "is_approved", "like_count", "comment_count",
            "my_reaction", "created_at",
        ]
        read_only_fields = ["like_count", "comment_count", "created_at", "my_reaction", "is_approved"]

    def get_my_reaction(self, obj):
        req = self.context.get("request")
        if not req or not req.user or not req.user.is_authenticated:
            return None
        r = obj.reactions.filter(user=req.user).first()
        return r.type if r else None

    def create(self, validated_data):
        req = self.context["request"]
        return Post.objects.create(user=req.user, **validated_data)
