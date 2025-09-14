# apps/posts/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Prefetch

from .models import Post, Comment, Reaction, CommentLike
from .serializers import PostSerializer, CommentSerializer
from .permissions import IsOwnerOrAdminOrReadOnly


def _user_min(u):
    return {
        "id": u.id,
        "email": getattr(u, "email", None),
        "username": getattr(u, "username", None),
    }

class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        like_qs = Reaction.objects.filter(type=Reaction.Type.LIKE).select_related("user").order_by("-created_at")
        return (
            Post.objects
            .select_related("user", "place", "itinerary")
            .prefetch_related(Prefetch("reactions", queryset=like_qs, to_attr="like_rows"))
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    # New feed
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticatedOrReadOnly])
    def feed(self, request):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)

    # Toggle like Post
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        with transaction.atomic():
            cur = Reaction.objects.filter(post=post, user=request.user, type=Reaction.Type.LIKE).first()
            if cur:
                cur.delete()
                my = None
            else:
                Reaction.objects.create(post=post, user=request.user, type=Reaction.Type.LIKE)
                my = Reaction.Type.LIKE

        like_qs = Reaction.objects.filter(post=post, type=Reaction.Type.LIKE).select_related("user").order_by("-created_at")
        like_count = like_qs.count()
        likers_preview = [_user_min(r.user) for r in like_qs[:3]]

        # đồng bộ cache
        Post.objects.filter(pk=post.pk).update(like_count=like_count)

        data = self.get_serializer(post).data
        data["my_reaction"] = my
        data["like_count"] = like_count
        data["likers_preview"] = likers_preview
        return Response(data, status=status.HTTP_200_OK)

    # Danh sách người đã like (full, có phân trang)
    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticatedOrReadOnly])
    def likes(self, request, pk=None):
        post = self.get_object()
        qs = Reaction.objects.filter(post=post, type=Reaction.Type.LIKE).select_related("user").order_by("-created_at")
        page = self.paginate_queryset(qs)
        items = [{"id": r.id, "user": _user_min(r.user), "created_at": r.created_at} for r in (page or qs)]
        return self.get_paginated_response(items) if page is not None else Response(items, status=status.HTTP_200_OK)

    # Comments root của Post
    @action(detail=True, methods=["get", "post"], permission_classes=[IsAuthenticatedOrReadOnly])
    def comments(self, request, pk=None):
        post = self.get_object()
        if request.method.lower() == "get":
            qs = post.comments.filter(parent__isnull=True).select_related("user").order_by("created_at")
            ser = CommentSerializer(qs, many=True, context={"request": request})
            return Response(ser.data)
        ser = CommentSerializer(data={"post": post.pk, **request.data}, context={"request": request})
        ser.is_valid(raise_exception=True)
        ser.save()
        post.refresh_from_db(fields=["comment_count"])  # signals
        return Response(ser.data, status=status.HTTP_201_CREATED)


class CommentViewSet(viewsets.GenericViewSet):
    queryset = Comment.objects.select_related("user", "post", "post__user")
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        return {"request": self.request}

    # Toggle like Comment
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        comment = self.get_object()
        with transaction.atomic():
            cur = CommentLike.objects.filter(comment=comment, user=request.user).first()
            liked = False
            if cur:
                cur.delete()
            else:
                CommentLike.objects.create(comment=comment, user=request.user)
                liked = True
        comment.refresh_from_db(fields=["like_count"])  # signals
        data = CommentSerializer(comment, context={"request": self.request}).data
        data["my_like"] = liked
        return Response(data, status=status.HTTP_200_OK)

    # Reply
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def reply(self, request, pk=None):
        parent = self.get_object()
        payload = {"post": parent.post_id, "parent": parent.pk, "content": request.data.get("content", "")}
        ser = CommentSerializer(data=payload, context={"request": request})
        ser.is_valid(raise_exception=True)
        ser.save()
        parent.post.refresh_from_db(fields=["comment_count"])  # signals
        return Response(ser.data, status=status.HTTP_201_CREATED)

    # DELETE comment với quy tắc quyền
    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        u = request.user
        if not u.is_authenticated:
            return Response({"detail": "Authentication required"}, status=401)
        if not (u.is_staff or comment.user_id == u.id or comment.post.user_id == u.id):
            return Response({"detail": "Not allowed"}, status=403)
        comment.delete()
        return Response(status=204)