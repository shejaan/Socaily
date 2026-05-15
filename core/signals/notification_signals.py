"""
core/signals/notification_signals.py
--------------------------------------
Signals that fire after Like / Comment / Follow to create notifications.
These are lightweight and delegate to notification_service for actual logic.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import Like, Comment, Follow
from core.services.notification_service import (
    create_like_notification,
    create_comment_notification,
    create_follow_notification,
)


@receiver(post_save, sender=Like)
def on_like_created(sender, instance, created, **kwargs):
    if created:
        create_like_notification(sender=instance.user, post=instance.post)


@receiver(post_save, sender=Comment)
def on_comment_created(sender, instance, created, **kwargs):
    if created:
        create_comment_notification(sender=instance.user, post=instance.post)


@receiver(post_save, sender=Follow)
def on_follow_created(sender, instance, created, **kwargs):
    if created:
        create_follow_notification(sender=instance.follower, receiver=instance.following)
