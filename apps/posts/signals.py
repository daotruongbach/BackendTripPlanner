from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Count
from .models import Post, Comment, Reaction

def _recount_post(post_id):
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return
    post.comment_count = Comment.objects.filter(post_id=post_id).count()
    post.like_count = Reaction.objects.filter(post_id=post_id).count()  # đếm mọi loại cảm xúc
    post.save(update_fields=["comment_count", "like_count"])

@receiver(post_save, sender=Comment)
def on_comment_created(sender, instance, created, **kwargs):
    if created:
        _recount_post(instance.post_id)

@receiver(post_delete, sender=Comment)
def on_comment_deleted(sender, instance, **kwargs):
    _recount_post(instance.post_id)

@receiver(post_save, sender=Reaction)
def on_reaction_saved(sender, instance, **kwargs):
    _recount_post(instance.post_id)

@receiver(post_delete, sender=Reaction)
def on_reaction_deleted(sender, instance, **kwargs):
    _recount_post(instance.post_id)
