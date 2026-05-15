"""
story_views.py
--------------
Handles story upload, viewing, seen-state tracking, and expiry.
Stories auto-expire after 24 h (enforced via queryset filter + model helper).
"""

from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import Story, StoryView
from core.services.follow_service import get_following_ids


def _active_stories():
    """Return queryset of non-expired stories."""
    cutoff = timezone.now() - timedelta(hours=24)
    return Story.objects.filter(created_at__gte=cutoff)


# ─────────────────────────────────────────────
#  UPLOAD STORY
# ─────────────────────────────────────────────

@login_required
@require_POST
def upload_story(request):
    """Upload a new story image.  Returns JSON for AJAX callers."""
    image   = request.FILES.get('image')
    caption = request.POST.get('caption', '').strip()[:200]

    if not image:
        return JsonResponse({'success': False, 'error': 'No image provided.'}, status=400)

    if image.size > 10 * 1024 * 1024:
        return JsonResponse({'success': False, 'error': 'Image must be under 10 MB.'}, status=400)

    story = Story.objects.create(user=request.user, image=image, caption=caption)

    return JsonResponse({
        'success':   True,
        'story': {
            'id':        story.id,
            'image_url': story.image.url,
            'caption':   story.caption,
            'username':  request.user.username,
        },
    })


# ─────────────────────────────────────────────
#  VIEW STORY (mark as seen)
# ─────────────────────────────────────────────

@login_required
def view_story(request, story_id):
    """
    GET  → returns story data as JSON (and marks it seen).
    Used by the frontend story-viewer modal.
    """
    story = get_object_or_404(_active_stories(), id=story_id)

    view_count = 0
    viewers = []
    is_owner = story.user == request.user
    if is_owner:
        story_views = StoryView.objects.filter(story=story).select_related('viewer')
        view_count = story_views.count()
        viewers = [{'username': v.viewer.username, 'avatar': v.viewer.profile.profile_image.url if hasattr(v.viewer, 'profile') and v.viewer.profile.profile_image else None} for v in story_views]
    else:
        # Record view (ignore if already viewed)
        StoryView.objects.get_or_create(story=story, viewer=request.user)

    return JsonResponse({
        'id':         story.id,
        'image_url':  story.image.url,
        'caption':    story.caption,
        'username':   story.user.username,
        'avatar_url': (
            story.user.profile.profile_image.url
            if hasattr(story.user, 'profile') and story.user.profile.profile_image
            else None
        ),
        'created_at': story.created_at.strftime('%H:%M'),
        'is_owner':   is_owner,
        'view_count': view_count,
        'viewers':    viewers,
    })


# ─────────────────────────────────────────────
#  USER STORIES LIST  (AJAX)
# ─────────────────────────────────────────────

@login_required
def user_stories(request, username):
    """Return JSON list of active stories for a given user."""
    target = get_object_or_404(User, username=username)
    stories = _active_stories().filter(user=target).order_by('created_at')

    seen_ids = set(
        StoryView.objects
        .filter(story__in=stories, viewer=request.user)
        .values_list('story_id', flat=True)
    )

    data = [{
        'id':         s.id,
        'image_url':  s.image.url,
        'caption':    s.caption,
        'seen':       s.id in seen_ids,
        'created_at': s.created_at.strftime('%H:%M'),
    } for s in stories]

    return JsonResponse({'stories': data, 'username': username})


# ─────────────────────────────────────────────
#  STORY FEED DATA  (used by home_view context)
# ─────────────────────────────────────────────

def get_story_users(me):
    """
    Returns a list of User objects (with story_seen annotation) who have
    active stories and are followed by `me`.  Used in home_view context.
    """
    cutoff = timezone.now() - timedelta(hours=24)
    following_ids = get_following_ids(me)

    # Users who have at least one active story and are followed by me
    story_user_ids = (
        Story.objects
        .filter(created_at__gte=cutoff, user_id__in=following_ids)
        .values_list('user_id', flat=True)
        .distinct()
    )

    users = (
        User.objects
        .filter(id__in=story_user_ids)
        .select_related('profile')
    )

    # Determine seen status per user (all stories seen → user ring is grey)
    result = []
    for user in users:
        user_stories_qs = Story.objects.filter(user=user, created_at__gte=cutoff)
        seen_count = StoryView.objects.filter(story__in=user_stories_qs, viewer=me).count()
        user.story_seen = (seen_count >= user_stories_qs.count()) and user_stories_qs.exists()
        user.latest_story_id = user_stories_qs.order_by('-created_at').values_list('id', flat=True).first()
        result.append(user)

    return result


# ─────────────────────────────────────────────
#  DELETE STORY
# ─────────────────────────────────────────────

@login_required
@require_POST
def delete_story(request, story_id):
    """Delete a story if the current user owns it."""
    story = get_object_or_404(Story, id=story_id)
    if story.user != request.user:
        return JsonResponse({'success': False, 'error': 'Not authorized.'}, status=403)
    
    story.delete()
    return JsonResponse({'success': True})
