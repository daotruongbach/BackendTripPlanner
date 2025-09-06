from rest_framework import serializers
from .models import Review

class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Review
        fields = ('id','place','user','user_email','rating','comment','is_approved','created_at')
        read_only_fields = ('user','is_approved','created_at')

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)