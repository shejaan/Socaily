"""
core/signals/profile_signals.py
---------------------------------
Auto-creates a Profile whenever a new User is created.
"""

from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

from core.models import Profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a Profile row automatically when a new User is saved."""
    if created:
        Profile.objects.get_or_create(user=instance)
