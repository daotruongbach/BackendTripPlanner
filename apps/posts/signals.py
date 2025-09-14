# apps/posts/signals.py
from django.db.models import F
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Post, Comment, Reaction, CommentLike

# ===== Post like_count từ Reaction(type=LIKE)
@receiver(post_save, sender=Reaction)
def _inc_post_like_count(sender, instance, created, **kwargs):
    if created and instance.type == Reaction.Type.LIKE:
        Post.objects.filter(pk=instance.post_id).update(like_count=F("like_count") + 1)

@receiver(post_delete, sender=Reaction)
def _dec_post_like_count(sender, instance, **kwargs):
    if instance.type == Reaction.Type.LIKE:
        Post.objects.filter(pk=instance.post_id).update(like_count=F("like_count") - 1)

# ===== Comment like_count từ CommentLike
@receiver(post_save, sender=CommentLike)
def _inc_comment_like_count(sender, instance, created, **kwargs):
    if created:
        Comment.objects.filter(pk=instance.comment_id).update(like_count=F("like_count") + 1)

@receiver(post_delete, sender=CommentLike)
def _dec_comment_like_count(sender, instance, **kwargs):
    Comment.objects.filter(pk=instance.comment_id).update(like_count=F("like_count") - 1)

# ===== Post comment_count từ Comment (đếm root + reply)
@receiver(post_save, sender=Comment)
def _inc_post_comment_count(sender, instance, created, **kwargs):
    if created:
        Post.objects.filter(pk=instance.post_id).update(comment_count=F("comment_count") + 1)

@receiver(post_delete, sender=Comment)
def _dec_post_comment_count(sender, instance, **kwargs):
    Post.objects.filter(pk=instance.post_id).update(comment_count=F("comment_count") - 1)