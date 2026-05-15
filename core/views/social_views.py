"""
social_views.py
---------------
Handles all social interactions:
  - Likes
  - Comments (with spam protection)
  - Save / unsave posts
  - Follow / unfollow
  - Accept / decline follow requests
  - Notifications
"""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import Post, Comment, Follow, FollowRequest, Notification
from core.services.like_service   import toggle_like
from core.services.follow_service import (
    follow_user   as svc_follow_user,
    unfollow_user as svc_unfollow_user,
    accept_follow_request  as svc_accept,
    decline_follow_request as svc_decline,
)

from django.shortcuts import render


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


# ─────────────────────────────────────────────
#  LIKE POST
# ─────────────────────────────────────────────

@login_required
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    liked, like_count = toggle_like(request.user, post)

    if _is_ajax(request):
        return JsonResponse({'liked': liked, 'like_count': like_count})

    return redirect(request.META.get('HTTP_REFERER', 'home'))


# ─────────────────────────────────────────────
#  COMMENT  (with anti-spam guard)
# ─────────────────────────────────────────────

@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    text = request.POST.get('text', '').strip()

    if not text:
        if _is_ajax(request):
            return JsonResponse({'success': False, 'error': 'Comment cannot be empty.'}, status=400)
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    # Truncate to Socaily's max comment length
    if len(text) > 2200:
        text = text[:2200]

    # Anti-spam: block if the same user commented on this post within the last 10 s
    spam_window = timezone.now() - timedelta(seconds=10)
    if Comment.objects.filter(user=request.user, post=post, created_at__gte=spam_window).exists():
        if _is_ajax(request):
            return JsonResponse(
                {'success': False, 'error': 'You are commenting too fast. Please slow down.'},
                status=429,
            )
        messages.error(request, 'You are commenting too fast.')
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    comment = Comment.objects.create(user=request.user, post=post, text=text)

    if post.user != request.user:
        Notification.objects.get_or_create(
            sender=request.user,
            receiver=post.user,
            post=post,
            notif_type='comment',
        )

    if _is_ajax(request):
        return JsonResponse({
            'success':  True,
            'comment': {
                'id':       comment.id,
                'text':     comment.text,
                'username': request.user.username,
                'avatar':   (
                    request.user.profile.profile_image.url
                    if hasattr(request.user, 'profile') and request.user.profile.profile_image
                    else None
                ),
            },
        })

    return redirect(request.META.get('HTTP_REFERER', 'home'))


# ─────────────────────────────────────────────
#  SAVE POST
# ─────────────────────────────────────────────

@login_required
@require_POST
def save_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Use .filter().exists() — avoids fetching the entire M2M set
    if post.saved_by.filter(id=request.user.id).exists():
        post.saved_by.remove(request.user)
        saved = False
    else:
        post.saved_by.add(request.user)
        saved = True

    if _is_ajax(request):
        return JsonResponse({'saved': saved})

    return redirect(request.META.get('HTTP_REFERER', 'home'))


# ─────────────────────────────────────────────
#  FOLLOW / UNFOLLOW
# ─────────────────────────────────────────────

@login_required
@require_POST
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)

    if user_to_follow == request.user:
        return redirect('profile', username=username)

    status = svc_follow_user(request.user, user_to_follow)
    
    if _is_ajax(request):
        return JsonResponse({'status': status})
        
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
@require_POST
def unfollow_user(request, username):
    user_to_unfollow = get_object_or_404(User, username=username)
    svc_unfollow_user(request.user, user_to_unfollow)

    if _is_ajax(request):
        return JsonResponse({'unfollowed': True})

    return redirect(request.META.get('HTTP_REFERER', 'home'))


# ─────────────────────────────────────────────
#  ACCEPT / DECLINE FOLLOW REQUEST
# ─────────────────────────────────────────────

@login_required
@require_POST
def accept_follow_request(request, request_id):
    follow_request = get_object_or_404(FollowRequest, id=request_id, receiver=request.user)
    svc_accept(follow_request)
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
@require_POST
def decline_follow_request(request, request_id):
    follow_request = get_object_or_404(FollowRequest, id=request_id, receiver=request.user)
    svc_decline(follow_request)
    return redirect(request.META.get('HTTP_REFERER', 'home'))


# ─────────────────────────────────────────────
#  NOTIFICATIONS
# ─────────────────────────────────────────────

@login_required
def notifications_view(request):
    notifs = (
        Notification.objects
        .filter(receiver=request.user)
        .select_related('sender', 'sender__profile', 'post')
        .order_by('-created_at')
    )
    # Mark all as read on page visit
    notifs.filter(is_read=False).update(is_read=True)

    return render(request, 'notifications.html', {'notifications': notifs})


@login_required
def mark_notification_read(request, notif_id):
    """AJAX endpoint to mark a single notification as read."""
    Notification.objects.filter(id=notif_id, receiver=request.user).update(is_read=True)
    return JsonResponse({'success': True})

@login_required
@require_POST
def mark_all_notifications_read(request):
    """AJAX endpoint to mark all notifications as read."""
    Notification.objects.filter(receiver=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})

@login_required
def poll_updates_api(request):
    """
    Polling endpoint for JS to fetch real-time updates (notifications, posts, messages).
    """
    unread_notifs = Notification.objects.filter(receiver=request.user, is_read=False).count()
    unread_msgs   = Message.objects.filter(receiver=request.user, is_read=False).count()
    
    from core.services.feed_service import get_feed_queryset
    latest_post = get_feed_queryset(request.user).first()
    latest_post_id = latest_post.id if latest_post else 0
    
    return JsonResponse({
        'unread_notifs': unread_notifs,
        'unread_msgs':   unread_msgs,
        'latest_post_id': latest_post_id
    })
