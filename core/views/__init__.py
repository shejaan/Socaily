"""
core/views/__init__.py
----------------------
Re-exports every view so that config/urls.py can continue to use the
single import  `from core import views`  without any URL changes.
"""

from core.views.auth_views    import (
    register_view,
    login_view,
    logout_view,
    check_availability,
)

from core.views.post_views    import (
    home_view,
    create_post,
    edit_post,
    delete_post,
    explore_view,
    saved_posts_view,
    search_view,
    profile_view,
    profile_edit,
    suggested_users_view,
    switch_account_view,
    share_post,
    feed_api,
)

from core.views.social_views  import (
    like_post,
    add_comment,
    save_post,
    follow_user,
    unfollow_user,
    accept_follow_request,
    decline_follow_request,
    notifications_view,
    mark_notification_read,
    mark_all_notifications_read,
    poll_updates_api,
)

from core.views.message_views import (
    messages_view,
    get_conversations,
    get_messages,
    send_message,
    edit_message,
    delete_message,
)

from core.views.story_views import (
    upload_story,
    view_story,
    user_stories,
    delete_story,
)

__all__ = [
    # auth
    'register_view', 'login_view', 'logout_view', 'check_availability',
    # posts / feed
    'home_view', 'create_post', 'edit_post', 'delete_post', 'explore_view',
    'saved_posts_view', 'search_view', 'profile_view', 'profile_edit',
    'suggested_users_view', 'switch_account_view', 'share_post', 'feed_api',
    # social
    'like_post', 'add_comment', 'save_post',
    'follow_user', 'unfollow_user',
    'accept_follow_request', 'decline_follow_request',
    'notifications_view', 'mark_notification_read', 'mark_all_notifications_read', 'poll_updates_api',
    # messages
    'messages_view', 'get_conversations', 'get_messages', 'send_message',
    'edit_message', 'delete_message',
    # stories
    'upload_story', 'view_story', 'user_stories',
]
