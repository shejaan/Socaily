from django.contrib import admin
from django.urls     import path, include
from django.conf     import settings
from django.conf.urls.static import static

from core import views

urlpatterns = [

    # ── Admin ──
    path('admin/', admin.site.urls),

    # ── Auth ──
    path('accounts/', include('allauth.urls')),
    path('register/', views.register_view, name='register'),
    path('signup/',   views.register_view, name='signup'),   # alias
    path('login/',    views.login_view,    name='login'),
    path('logout/',   views.logout_view,   name='logout'),
    path('check-availability/', views.check_availability, name='check_availability'),

    # ── Home Feed ──
    path('', views.home_view, name='home'),

    # ── Profile ──
    path('profile/edit/',           views.profile_edit, name='profile_edit'),
    path('profile/<str:username>/', views.profile_view, name='profile'),

    # ── Posts ──
    path('create-post/',              views.create_post,  name='create_post'),
    path('edit-post/<int:post_id>/',  views.edit_post,    name='edit_post'),
    path('delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('like/<int:post_id>/',       views.like_post,    name='like_post'),
    path('comment/<int:post_id>/',    views.add_comment,  name='add_comment'),
    path('save/<int:post_id>/',       views.save_post,    name='save_post'),
    path('share/<int:post_id>/',      views.share_post,   name='share_post'),

    # ── Feed API (infinite scroll) ──
    path('api/feed/', views.feed_api, name='feed_api'),

    # ── Follow ──
    path('follow/<str:username>/',           views.follow_user,            name='follow_user'),
    path('unfollow/<str:username>/',         views.unfollow_user,          name='unfollow_user'),
    path('accept-follow/<int:request_id>/',  views.accept_follow_request,  name='accept_follow_request'),
    path('decline-follow/<int:request_id>/', views.decline_follow_request, name='decline_follow_request'),

    # ── Notifications ──
    path('notifications/',                       views.notifications_view,     name='notifications'),
    path('notifications/<int:notif_id>/read/',   views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/',              views.mark_all_notifications_read, name='mark_all_notifications_read'),

    # ── Explore ──
    path('explore/', views.explore_view, name='explore'),

    # ── Saved Posts ──
    path('saved/', views.saved_posts_view, name='saved_posts'),

    # ── Messages ──
    path('messages/',                       views.messages_view,    name='messages'),
    path('messages/conversations/',         views.get_conversations, name='get_conversations'),
    path('messages/with/<str:username>/',   views.get_messages,     name='get_messages'),
    path('messages/send/<str:username>/',   views.send_message,     name='send_message'),

    # ── Search ──
    path('search/', views.search_view, name='search'),

    # ── Stories ──
    path('stories/upload/',                  views.upload_story,  name='upload_story'),
    path('stories/view/<int:story_id>/',     views.view_story,    name='view_story'),
    path('stories/delete/<int:story_id>/',   views.delete_story,  name='delete_story'),
    path('stories/<str:username>/',          views.user_stories,  name='user_stories'),

    # ── Misc ──
    path('suggested-users/', views.suggested_users_view, name='suggested_users'),
    # switch_account kept as stub (redirects to login) so no template refs break
    path('switch-account/',  views.switch_account_view,  name='switch_account'),

]

# Serve media files locally in development only
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)