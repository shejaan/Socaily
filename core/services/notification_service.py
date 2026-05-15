"""
core/services/notification_service.py
--------------------------------------
Centralised notification creation / querying.
All notification logic lives here; views and signals call these functions.
"""

from django.contrib.auth.models import User

from core.models import Notification, Post
from core.utils.constants import (
    NOTIF_LIKE,
    NOTIF_COMMENT,
    NOTIF_FOLLOW,
    NOTIF_FOLLOW_REQUEST,
)


def create_notification(
    sender: User,
    receiver: User,
    notif_type: str,
    post: Post | None = None,
) -> Notification | None:
    """
    Create a notification if sender != receiver.
    Uses get_or_create to avoid duplicates for follow / follow_request types.
    Returns the Notification instance or None if sender == receiver.
    """
    if sender == receiver:
        return None

    notif, _ = Notification.objects.get_or_create(
        sender=sender,
        receiver=receiver,
        notif_type=notif_type,
        post=post,
        defaults={'is_read': False},
    )
    return notif


def create_like_notification(sender: User, post: Post) -> Notification | None:
    return create_notification(sender, post.user, NOTIF_LIKE, post=post)


def create_comment_notification(sender: User, post: Post) -> Notification | None:
    return create_notification(sender, post.user, NOTIF_COMMENT, post=post)


def create_follow_notification(sender: User, receiver: User) -> Notification | None:
    return create_notification(sender, receiver, NOTIF_FOLLOW)


def create_follow_request_notification(sender: User, receiver: User) -> Notification | None:
    return create_notification(sender, receiver, NOTIF_FOLLOW_REQUEST)


def get_unread_count(user: User) -> int:
    """Return the count of unread notifications for a user."""
    return Notification.objects.filter(receiver=user, is_read=False).count()


def mark_all_read(user: User) -> int:
    """Mark all unread notifications as read. Returns count updated."""
    return Notification.objects.filter(receiver=user, is_read=False).update(is_read=True)


def mark_one_read(notif_id: int, user: User) -> bool:
    """Mark a single notification as read. Returns True if updated."""
    updated = Notification.objects.filter(id=notif_id, receiver=user).update(is_read=True)
    return updated > 0


def get_notifications_qs(user: User):
    """Return the full notifications queryset for a user, ordered newest first."""
    return (
        Notification.objects
        .filter(receiver=user)
        .select_related('sender', 'sender__profile', 'post')
        .order_by('-created_at')
    )
