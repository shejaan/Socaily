"""
like_service.py
---------------
Toggle a like on a post and fire the notification in one place.
"""

from core.models import Like, Notification


def toggle_like(user, post):
    """
    Toggle the like on *post* by *user*.

    Returns:
        liked (bool)  – True if the post is now liked, False if unliked.
        like_count (int) – Updated total like count for the post.
    """
    existing = Like.objects.filter(user=user, post=post)

    if existing.exists():
        existing.delete()
        liked = False
    else:
        Like.objects.create(user=user, post=post)
        liked = True

        # Notify the post owner (skip self-likes)
        if post.user != user:
            Notification.objects.get_or_create(
                sender=user,
                receiver=post.user,
                post=post,
                notif_type='like',
            )

    like_count = post.likes.count()
    return liked, like_count
