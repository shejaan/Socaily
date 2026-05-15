"""
post_views.py
-------------
Handles post display, creation, deletion, editing, sharing, feed, explore,
saved posts, search, profile, and miscellaneous page views.
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from core.forms  import ProfileEditForm
from core.models import Post, Like, Follow, FollowRequest, Notification, Profile, Conversation, Message
from core.services.feed_service   import get_feed_queryset, get_liked_and_saved_ids
from core.services.follow_service import get_following_ids, get_sent_request_ids

logger = logging.getLogger(__name__)


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


# ─────────────────────────────────────────────
#  HOME FEED
# ─────────────────────────────────────────────

@login_required
def home_view(request):
    me = request.user

    followed_ids = get_following_ids(me)
    sent_req_ids = get_sent_request_ids(me)

    posts_qs  = get_feed_queryset(me)
    paginator = Paginator(posts_qs, 5)          # only 5 posts initially
    page_obj  = paginator.get_page(1)

    # Sidebar data
    follower_ids = list(
        Follow.objects.filter(following=me).values_list('follower_id', flat=True)
    )
    # Notifications logic moved to core.utils.context_processors.notifications_context

    # Suggested users ordered by follower count
    suggested_users = (
        User.objects
        .exclude(id=me.id)
        .exclude(id__in=followed_ids)
        .exclude(id__in=sent_req_ids)
        .annotate(follower_count=Count('follower_set'))
        .order_by('-follower_count')
        .select_related('profile')
        [:5]
    )

    page_post_ids = [p.id for p in page_obj.object_list]
    liked_ids, saved_ids = get_liked_and_saved_ids(me, page_post_ids)

    # Stories for people I follow
    from core.views.story_views import get_story_users
    story_users = get_story_users(me)

    from core.models import Story
    from django.utils import timezone
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(hours=24)
    my_active_stories = Story.objects.filter(user=me, created_at__gte=cutoff)
    has_own_story = my_active_stories.exists()
    own_latest_story_id = my_active_stories.order_by('-created_at').values_list('id', flat=True).first() if has_own_story else None

    context = {
        'page_obj':                   page_obj,
        'posts':                      page_obj.object_list,
        'suggested_users':            suggested_users,
        'following_ids':              followed_ids,
        'sent_request_ids':           sent_req_ids,
        'follower_ids':               follower_ids,
        'liked_ids':                  liked_ids,
        'saved_ids':                  saved_ids,
        'story_users':                story_users,
        'has_own_story':              has_own_story,
        'own_latest_story_id':        own_latest_story_id,
        'has_more_posts':             page_obj.has_next(),
    }

    return render(request, 'homepage.html', context)


# ─────────────────────────────────────────────
#  PROFILE
# ─────────────────────────────────────────────

@login_required
def profile_view(request, username):
    profile_user = get_object_or_404(
        User.objects.select_related('profile'), username=username
    )

    posts = (
        Post.objects
        .filter(user=profile_user)
        .prefetch_related('likes', 'comments')
        .order_by('-created_at')
    )
    post_count = posts.count()  # evaluated once

    followers_qs = Follow.objects.filter(following=profile_user).select_related('follower', 'follower__profile')
    following_qs = Follow.objects.filter(follower=profile_user).select_related('following', 'following__profile')

    followers_list = [f.follower  for f in followers_qs]
    following_list = [f.following for f in following_qs]

    is_following     = Follow.objects.filter(follower=request.user, following=profile_user).exists()
    has_sent_request = FollowRequest.objects.filter(sender=request.user, receiver=profile_user).exists()

    can_see_posts = (
        not profile_user.profile.private_account
        or profile_user == request.user
        or is_following
    )

    from core.models import Story
    from django.utils import timezone
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(hours=24)
    active_stories = Story.objects.filter(user=profile_user, created_at__gte=cutoff)
    has_story = active_stories.exists()
    latest_story_id = active_stories.order_by('-created_at').values_list('id', flat=True).first() if has_story else None

    page_post_ids = [p.id for p in posts] if can_see_posts else []
    liked_ids, saved_ids = get_liked_and_saved_ids(request.user, page_post_ids)

    context = {
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
        'has_story':        has_story,
        'latest_story_id':  latest_story_id,
        'liked_ids':        liked_ids,
        'saved_ids':        saved_ids,
    }

    return render(request, 'profile.html', context)


@login_required
def profile_edit(request):
    """Edit the logged-in user's profile (bio, image, website, privacy)."""
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        fullname = request.POST.get('fullname', '').strip()
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            if fullname:
                request.user.first_name = fullname
                request.user.save(update_fields=['first_name'])
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile', username=request.user.username)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ProfileEditForm(instance=profile)

    return render(request, 'profile_edit.html', {
        'form': form,
        'profile': profile,
    })


# ─────────────────────────────────────────────
#  CREATE / EDIT / DELETE POST
# ─────────────────────────────────────────────

@login_required
def create_post(request):

    if request.method == 'POST':
        image    = request.FILES.get('image')
        caption  = request.POST.get('caption', '').strip()
        location = request.POST.get('location', '').strip()
        is_ajax  = _is_ajax(request)

        if not image:
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'Please select an image.'})
            messages.error(request, 'Please select an image.')
            return redirect('home')

        # Basic size guard (10 MB)
        if image.size > 10 * 1024 * 1024:
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'Image must be smaller than 10 MB.'})
            messages.error(request, 'Image must be smaller than 10 MB.')
            return redirect('home')

        post = Post.objects.create(
            user=request.user,
            image=image,
            caption=caption,
            location=location,
        )

        if is_ajax:
            return JsonResponse({
                'success':   True,
                'message':   'Post shared successfully! 🎉',
                'post': {
                    'id':        post.id,
                    'image_url': post.image.url,
                    'caption':   post.caption,
                    'username':  request.user.username,
                },
            })

        messages.success(request, 'Post shared successfully! 🎉')

    return redirect('home')


@login_required
@require_POST
def edit_post(request, post_id):
    """Edit caption/location — only the post owner."""
    post = get_object_or_404(Post, id=post_id, user=request.user)
    post.caption  = request.POST.get('caption', post.caption).strip()
    post.location = request.POST.get('location', post.location).strip()
    post.save(update_fields=['caption', 'location'])
    if _is_ajax(request):
        return JsonResponse({'success': True, 'caption': post.caption, 'location': post.location})
    messages.success(request, 'Post updated.')
    return redirect('profile', username=request.user.username)


@login_required
@require_POST
def delete_post(request, post_id):
    """Delete a post — only the owner can do this."""
    post = get_object_or_404(Post, id=post_id, user=request.user)
    post.delete()
    if _is_ajax(request):
        return JsonResponse({'success': True})
    messages.success(request, 'Post deleted.')
    return redirect('profile', username=request.user.username)


@login_required
def share_post(request, post_id):
    """
    Share a post:
    - GET  → returns post URL as JSON (for 'copy link')
    - POST → optionally sends a DM with the post link to a target user
    """
    post = get_object_or_404(Post, id=post_id)
    post_url = request.build_absolute_uri(f'/p/{post_id}/')

    if request.method == 'POST':
        target_username = request.POST.get('username', '').strip()
        if target_username:
            target = User.objects.filter(username=target_username).first()
            if target and target != request.user:
                conv, _ = Conversation.get_or_create_for(request.user, target)
                msg_text = f"Check out this post: {post_url}"
                Message.objects.create(
                    conversation=conv,
                    sender=request.user,
                    receiver=target,
                    text=msg_text,
                )
                conv.save(update_fields=['updated_at'])
                return JsonResponse({'success': True, 'sent': True, 'url': post_url})
        return JsonResponse({'success': True, 'sent': False, 'url': post_url})

    return JsonResponse({'success': True, 'url': post_url})


# ─────────────────────────────────────────────
#  INFINITE SCROLL FEED API
# ─────────────────────────────────────────────

@login_required
def feed_api(request):
    """
    AJAX endpoint for infinite scroll.
    GET /api/feed/?page=<N>  → JSON with post cards HTML + has_next flag.
    """
    me        = request.user
    page_num  = request.GET.get('page', 2)

    followed_ids = get_following_ids(me)
    sent_req_ids = get_sent_request_ids(me)

    posts_qs  = get_feed_queryset(me)
    paginator = Paginator(posts_qs, 5)
    page_obj  = paginator.get_page(page_num)

    page_post_ids = [p.id for p in page_obj.object_list]
    liked_ids, saved_ids = get_liked_and_saved_ids(me, page_post_ids)

    posts_data = []
    for post in page_obj.object_list:
        posts_data.append({
            'id':          post.id,
            'image_url':   post.image.url if post.image else '',
            'caption':     post.caption,
            'location':    post.location,
            'username':    post.user.username,
            'avatar_url':  (
                post.user.profile.profile_image.url
                if hasattr(post.user, 'profile') and post.user.profile.profile_image
                else None
            ),
            'like_count':  post.likes.count(),
            'comment_count': post.comments.count(),
            'liked':       post.id in liked_ids,
            'saved':       post.id in saved_ids,
            'is_owner':    post.user_id == me.id,
            'created_at':  post.created_at.strftime('%Y-%m-%dT%H:%M:%S'),
        })

    return JsonResponse({
        'posts':    posts_data,
        'has_next': page_obj.has_next(),
        'page':     page_obj.number,
    })


# ─────────────────────────────────────────────
#  EXPLORE
# ─────────────────────────────────────────────

@login_required
def explore_view(request):
    """Show trending public posts (ordered by like count), paginated."""
    posts_qs = (
        Post.objects
        .filter(user__profile__private_account=False)
        .annotate(like_count=Count('likes'))
        .select_related('user', 'user__profile')
        .prefetch_related('likes', 'comments')
        .order_by('-like_count', '-created_at')
    )
    paginator = Paginator(posts_qs, 24)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    page_post_ids = [p.id for p in page_obj.object_list]
    liked_ids, saved_ids = get_liked_and_saved_ids(request.user, page_post_ids)

    return render(request, 'explore.html', {
        'page_obj':  page_obj,
        'posts':     page_obj.object_list,
        'liked_ids': liked_ids,
        'saved_ids': saved_ids,
    })


# ─────────────────────────────────────────────
#  SAVED POSTS
# ─────────────────────────────────────────────

@login_required
def saved_posts_view(request):
    posts_qs = (
        request.user.saved_posts
        .select_related('user', 'user__profile')
        .prefetch_related('likes', 'comments')
        .order_by('-created_at')
    )
    paginator = Paginator(posts_qs, 12)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'saved_posts.html', {
        'page_obj': page_obj,
        'posts':    page_obj.object_list,
    })


# ─────────────────────────────────────────────
#  SEARCH
# ─────────────────────────────────────────────

@login_required
def search_view(request):
    q           = request.GET.get('q', '').strip()
    return_json = request.GET.get('json') == '1'

    if return_json and q:
        users = (
            User.objects
            .filter(Q(username__icontains=q) | Q(first_name__icontains=q))
            .exclude(id=request.user.id)
            .select_related('profile')
            [:10]
        )
        data = [{
            'username':   u.username,
            'full_name':  u.get_full_name() or u.username,
            'avatar_url': (
                u.profile.profile_image.url
                if hasattr(u, 'profile') and u.profile.profile_image else None
            ),
        } for u in users]
        return JsonResponse({'users': data})

    return render(request, 'search.html', {'query': q})


# ─────────────────────────────────────────────
#  MISC
# ─────────────────────────────────────────────

@login_required
def suggested_users_view(request):
    """Full suggested-users page."""
    me           = request.user
    followed_ids = get_following_ids(me)
    sent_req_ids = get_sent_request_ids(me)

    users = (
        User.objects
        .exclude(id=me.id)
        .exclude(id__in=followed_ids)
        .exclude(id__in=sent_req_ids)
        .annotate(follower_count=Count('follower_set'))
        .order_by('-follower_count')
        .select_related('profile')
        [:20]
    )
    return render(request, 'suggested_users.html', {
        'suggested_users':  users,
        'following_ids':    followed_ids,
        'sent_request_ids': sent_req_ids,
    })


@login_required
def switch_account_view(request):
    return redirect('login')
