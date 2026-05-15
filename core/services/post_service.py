"""
core/services/post_service.py
------------------------------
Business logic for post creation, editing, deletion, and querying.
"""

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from core.models import Post
from core.utils.constants import POST_IMAGE_MAX_BYTES, CAPTION_MAX_LENGTH
from core.services.media_service import validate_post_image


def create_post(user: User, image, caption: str, location: str) -> Post:
    """
    Validate and create a new Post.
    Raises ValidationError on invalid image.
    """
    validate_post_image(image)

    return Post.objects.create(
        user=user,
        image=image,
        caption=caption[:CAPTION_MAX_LENGTH].strip(),
        location=location.strip(),
    )


def edit_post(post: Post, caption: str, location: str) -> Post:
    """Update post caption and location."""
    post.caption  = caption[:CAPTION_MAX_LENGTH].strip()
    post.location = location.strip()
    post.save(update_fields=['caption', 'location'])
    return post


def delete_post(post: Post) -> None:
    """Delete a post (owner check must be done in the view)."""
    post.delete()


def get_post_for_owner(post_id: int, user: User) -> Post:
    """Fetch a post by ID, 404 if not found, 403 if not owner."""
    return get_object_or_404(Post, id=post_id, user=user)
