"""
core/utils/validators.py
------------------------
Reusable file and text validators used across views, services, and forms.
"""

from django.core.exceptions import ValidationError
from .constants import (
    ALLOWED_IMAGE_TYPES,
    PROFILE_IMAGE_MAX_BYTES,
    STORY_IMAGE_MAX_BYTES,
    POST_IMAGE_MAX_BYTES,
    COMMENT_MAX_LENGTH,
    MESSAGE_MAX_LENGTH,
)


def validate_image(image_file, max_bytes: int = POST_IMAGE_MAX_BYTES) -> None:
    """
    Validate an uploaded image file.

    Raises ValidationError if:
    - The file exceeds max_bytes
    - The MIME type is not in ALLOWED_IMAGE_TYPES

    Args:
        image_file: InMemoryUploadedFile or TemporaryUploadedFile
        max_bytes:  Maximum allowed file size in bytes
    """
    if not image_file:
        raise ValidationError("No image was provided.")

    if image_file.size > max_bytes:
        max_mb = max_bytes // (1024 * 1024)
        raise ValidationError(f"Image must be smaller than {max_mb} MB.")

    content_type = getattr(image_file, 'content_type', None)
    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError(
            f"Unsupported image type '{content_type}'. "
            "Allowed: JPEG, PNG, WebP, GIF."
        )


def validate_profile_image(image_file) -> None:
    validate_image(image_file, max_bytes=PROFILE_IMAGE_MAX_BYTES)


def validate_story_image(image_file) -> None:
    validate_image(image_file, max_bytes=STORY_IMAGE_MAX_BYTES)


def validate_post_image(image_file) -> None:
    validate_image(image_file, max_bytes=POST_IMAGE_MAX_BYTES)


def validate_text_length(text: str, max_length: int, field_name: str = "Text") -> str:
    """
    Strip whitespace and enforce max length.
    Returns the cleaned text string.
    Raises ValidationError if empty after stripping.
    """
    text = text.strip()
    if not text:
        raise ValidationError(f"{field_name} cannot be empty.")
    return text[:max_length]


def validate_comment(text: str) -> str:
    return validate_text_length(text, COMMENT_MAX_LENGTH, "Comment")


def validate_message(text: str) -> str:
    return validate_text_length(text, MESSAGE_MAX_LENGTH, "Message")
