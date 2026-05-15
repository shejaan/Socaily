"""
core/services/profile_service.py
---------------------------------
Business logic for user profile operations.
Views should call these functions instead of duplicating logic.
"""

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from core.models import Profile, Follow, FollowRequest, Post


def get_or_create_profile(user) -> Profile:
    """Return user's Profile, creating it if it doesn't exist."""
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


def get_profile_context(profile_user: User, request_user: User) -> dict:
    """
    Build the full context dict needed to render a profile page.
    Centralises the DB queries so the view stays thin.
    """
    posts = (
        Post.objects
        .filter(user=profile_user)
        .prefetch_related('likes', 'comments')
        .order_by('-created_at')
    )
    post_count = posts.count()

    followers_qs = (
        Follow.objects
        .filter(following=profile_user)
        .select_related('follower', 'follower__profile')
    )
    following_qs = (
        Follow.objects
        .filter(follower=profile_user)
        .select_related('following', 'following__profile')
    )

    followers_list = [f.follower  for f in followers_qs]
    following_list = [f.following for f in following_qs]

    is_following     = Follow.objects.filter(follower=request_user, following=profile_user).exists()
    has_sent_request = FollowRequest.objects.filter(sender=request_user, receiver=profile_user).exists()

    can_see_posts = (
        not profile_user.profile.private_account
        or profile_user == request_user
        or is_following
    )

    return {
        'profile_user':     profile_user,
        'posts':            posts if can_see_posts else [],
        'can_see_posts':    can_see_posts,
        'followers_list':   followers_list,
        'following_list':   following_list,
        'followers_count':  len(followers_list),
        'following_count':  len(following_list),
        'is_following':     is_following,
        'has_sent_request': has_sent_request,
        'post_count':       post_count,
    }


def update_profile(user: User, form_data: dict, files: dict) -> tuple[Profile, bool]:
    """
    Update a user's profile.

    Args:
        user:      The User instance to update.
        form_data: POST data dict (bio, website, private_account, fullname)
        files:     FILES dict for profile_image

    Returns:
        (profile, success) tuple
    """
    from core.forms import ProfileEditForm

    profile = get_or_create_profile(user)
    form = ProfileEditForm(form_data, files, instance=profile)

    if not form.is_valid():
        return profile, False

    form.save()

    fullname = form_data.get('fullname', '').strip()
    if fullname:
        user.first_name = fullname
        user.save(update_fields=['first_name'])

    return profile, True
