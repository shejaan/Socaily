"""
core/services/story_service.py
-------------------------------
Business logic for stories: creation, expiry, viewer tracking.
Extracted from story_views.py so it can be reused by tasks and consumers.
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone

from core.models import Story, StoryView
from core.utils.constants import STORY_EXPIRY_HOURS
from core.services.follow_service import get_following_ids
from core.services.media_service import validate_story_image


def active_stories_qs():
    """Return a queryset of non-expired stories."""
    cutoff = timezone.now() - timedelta(hours=STORY_EXPIRY_HOURS)
    return Story.objects.filter(created_at__gte=cutoff)


def create_story(user: User, image, caption: str = '') -> Story:
    """Validate and create a new story."""
    validate_story_image(image)
    return Story.objects.create(
        user=user,
        image=image,
        caption=caption[:200].strip(),
    )


def record_story_view(story: Story, viewer: User) -> None:
    """Record that viewer has seen this story (idempotent)."""
    if story.user != viewer:
        StoryView.objects.get_or_create(story=story, viewer=viewer)


def get_story_users_for_feed(me: User) -> list:
    """
    Return users followed by `me` who have active stories,
    annotated with `story_seen` and `latest_story_id`.
    """
    cutoff = timezone.now() - timedelta(hours=STORY_EXPIRY_HOURS)
    following_ids = get_following_ids(me)

    story_user_ids = (
        Story.objects
        .filter(created_at__gte=cutoff, user_id__in=following_ids)
        .values_list('user_id', flat=True)
        .distinct()
    )

    from django.contrib.auth.models import User as _User
    users = (
        _User.objects
        .filter(id__in=story_user_ids)
        .select_related('profile')
    )

    result = []
    for user in users:
        user_stories_qs = Story.objects.filter(user=user, created_at__gte=cutoff)
        seen_count = StoryView.objects.filter(story__in=user_stories_qs, viewer=me).count()
        user.story_seen = (seen_count >= user_stories_qs.count()) and user_stories_qs.exists()
        user.latest_story_id = (
            user_stories_qs.order_by('-created_at').values_list('id', flat=True).first()
        )
        result.append(user)

    return result


def expire_old_stories() -> int:
    """
    Delete stories older than STORY_EXPIRY_HOURS.
    Returns count of deleted stories.
    Used by Celery task.
    """
    cutoff = timezone.now() - timedelta(hours=STORY_EXPIRY_HOURS)
    deleted, _ = Story.objects.filter(created_at__lt=cutoff).delete()
    return deleted
