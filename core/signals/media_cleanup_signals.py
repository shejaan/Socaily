"""
core/signals/media_cleanup_signals.py
--------------------------------------
Deletes old media files from disk/Cloudinary when a Profile or Post image
is updated or the object is deleted.

Only deletes if the file actually changed (prevents deleting on non-image saves).
"""

import os
import logging

from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver

from core.models import Profile, Post, Story

logger = logging.getLogger(__name__)


def _delete_field_file(field):
    """Safely delete a FileField's file from storage."""
    if not field or not field.name:
        return
    try:
        storage = field.storage
        if storage.exists(field.name):
            storage.delete(field.name)
            logger.debug("Deleted media file: %s", field.name)
    except Exception as exc:
        logger.warning("Could not delete media file %s: %s", field.name, exc)


@receiver(pre_save, sender=Profile)
def cleanup_old_profile_image(sender, instance, **kwargs):
    """Delete old profile image when a new one is uploaded."""
    if not instance.pk:
        return
    try:
        old = Profile.objects.get(pk=instance.pk)
    except Profile.DoesNotExist:
        return
    if old.profile_image and old.profile_image != instance.profile_image:
        _delete_field_file(old.profile_image)


@receiver(post_delete, sender=Post)
def cleanup_post_image(sender, instance, **kwargs):
    """Delete post image when a post is deleted."""
    _delete_field_file(instance.image)


@receiver(post_delete, sender=Story)
def cleanup_story_image(sender, instance, **kwargs):
    """Delete story image when a story is deleted."""
    _delete_field_file(instance.image)
