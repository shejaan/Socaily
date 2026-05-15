"""
feed_service.py
---------------
Encapsulates the logic for building the home feed and
fetching liked/saved post IDs for a given user and page.
"""

from django.db.models import Count

from core.models import Post, Like, Follow


def get_feed_queryset(user):
    """
    Return the base queryset for a user's home feed:
    posts from followed users + the user's own posts,
    ordered by newest first with all necessary relations
    pre-fetched to avoid N+1 queries.
    """
    followed_ids = list(
        Follow.objects.filter(follower=user).values_list('following_id', flat=True)
    )
    feed_ids = followed_ids + [user.id]

    return (
        Post.objects
        .filter(user_id__in=feed_ids)
        .select_related('user', 'user__profile')
        .prefetch_related('likes', 'comments__user', 'saved_by')
        .order_by('-created_at')
    )


def get_liked_and_saved_ids(user, post_ids):
    """
    Given a user and a list of post IDs (e.g. from a paginated page),
    return two sets: liked_ids and saved_ids.

    Using sets + a single DB query per type keeps template rendering O(1).
    """
    liked_ids = set(
        Like.objects.filter(user=user, post_id__in=post_ids)
        .values_list('post_id', flat=True)
    )
    saved_ids = set(
        user.saved_posts.filter(id__in=post_ids)
        .values_list('id', flat=True)
    )
    return liked_ids, saved_ids
