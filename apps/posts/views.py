from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.db.models import Q

from .models import Post, Comment, Reaction
from .serializers import PostSerializer, CommentSerializer

class IsAdminOrOwnerOrReadOnly(IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        if request.user and request.user.is_authenticated:
            return request.user.is_staff or obj.user_id == request.user.id
        return False

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related("user", "place", "itinerary")
    serializer_class = PostSerializer
    permission_classes = [IsAdminOrOwnerOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user if self.request.user.is_authenticated else None
        # feed: chỉ bài đã duyệt; nếu có đăng nhập: cộng thêm bài của chính mình
        if u:
            return qs.filter(Q(is_approved=True) | Q(user=u))
        return qs.filter(is_approved=True)

    def perform_create(self, serializer):
        # nếu muốn duyệt tay, chuyển default False tại models.Post.is_approved
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        # admin có thể duyệt/ẩn bài
        if not request.user.is_staff and "is_approved" in request.data:
            return Response({"detail": "Chỉ admin được duyệt/ẩn bài."}, status=403)
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def comments(self, request, pk=None):
        post = self.get_object()
        content = request.data.get("content", "").strip()
        if not content:
            return Response({"detail": "Thiếu nội dung."}, status=400)
        cmt = Comment.objects.create(post=post, user=request.user, content=content)
        ser = CommentSerializer(cmt)
        return Response(ser.data, status=201)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticatedOrReadOnly])
    def list_comments(self, request, pk=None):
        post = self.get_object()
        qs = post.comments.select_related("user").all()
        page = self.paginate_queryset(qs)
        ser = CommentSerializer(page or qs, many=True)
        return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def react(self, request, pk=None):
        post = self.get_object()
        rtype = request.data.get("type", "LIKE")
        cur = post.reactions.filter(user=request.user).first()
        if cur and cur.type == rtype:
            cur.delete()  # toggle off
            my = None
        else:
            if cur:
                cur.type = rtype; cur.save()
            else:
                cur = Reaction.objects.create(post=post, user=request.user, type=rtype)
            my = cur.type
        post.refresh_from_db(fields=["like_count"])
        ser = self.get_serializer(post)
        data = ser.data
        data["my_reaction"] = my
        return Response(data)
from django.shortcuts import render

# Create your views here.
