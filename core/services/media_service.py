"""
core/services/media_service.py
------------------------------
Centralised media handling:
  - image validation (wraps utils.validators)
  - upload path generation
  - (future) WebP conversion, thumbnail generation
"""

import os
import uuid

from django.core.exceptions import ValidationError

from core.utils.constants import (
    ALLOWED_IMAGE_TYPES,
    PROFILE_IMAGE_MAX_BYTES,
    STORY_IMAGE_MAX_BYTES,
    POST_IMAGE_MAX_BYTES,
    UPLOAD_PATH_PROFILES,
    UPLOAD_PATH_POSTS,
    UPLOAD_PATH_STORIES,
    UPLOAD_PATH_MESSAGES,
)


# ── Upload path generators (used in model field upload_to) ────────────

def profile_upload_path(instance, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return f"{UPLOAD_PATH_PROFILES}{uuid.uuid4().hex}{ext}"


def post_upload_path(instance, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return f"{UPLOAD_PATH_POSTS}{uuid.uuid4().hex}{ext}"


def story_upload_path(instance, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return f"{UPLOAD_PATH_STORIES}{uuid.uuid4().hex}{ext}"


def message_upload_path(instance, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return f"{UPLOAD_PATH_MESSAGES}{uuid.uuid4().hex}{ext}"


# ── Validation ────────────────────────────────────────────────────────

def validate_image(image_file, max_bytes: int) -> None:
    """
    Validate an uploaded image.
    Raises ValidationError on failure.
    """
    if not image_file:
        raise ValidationError("No image was provided.")

    if image_file.size > max_bytes:
        max_mb = max_bytes // (1024 * 1024)
        raise ValidationError(f"Image must be smaller than {max_mb} MB.")

    content_type = getattr(image_file, 'content_type', None)
    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError(
            f"Unsupported image type. Allowed: JPEG, PNG, WebP, GIF."
        )


def validate_profile_image(image_file) -> None:
    validate_image(image_file, PROFILE_IMAGE_MAX_BYTES)


def validate_story_image(image_file) -> None:
    validate_image(image_file, STORY_IMAGE_MAX_BYTES)


def validate_post_image(image_file) -> None:
    validate_image(image_file, POST_IMAGE_MAX_BYTES)


# ── Helpers ───────────────────────────────────────────────────────────

def get_media_url(field) -> str | None:
    """Safely return a media field URL, or None if not set."""
    try:
        return field.url if field else None
    except ValueError:
        return None
