"""
core/websocket/routing.py
--------------------------
WebSocket URL routing for Django Channels.

To activate:
1. pip install channels channels-redis
2. Set ASGI_APPLICATION = 'config.asgi.application' in settings.py
3. Configure CHANNEL_LAYERS in settings.py
4. Replace config/wsgi.py usage with config/asgi.py in deployment
"""

try:
    from django.urls import re_path
    from channels.routing import ProtocolTypeRouter, URLRouter

    from core.websocket.auth import TokenAuthMiddlewareStack
    from core.consumers.chat_consumer         import ChatConsumer
    from core.consumers.notification_consumer import NotificationConsumer
    from core.consumers.presence_consumer     import PresenceConsumer

    websocket_urlpatterns = [
        re_path(r'ws/chat/(?P<conversation_id>\d+)/$', ChatConsumer.as_asgi()),
        re_path(r'ws/notifications/$',                 NotificationConsumer.as_asgi()),
        re_path(r'ws/presence/$',                      PresenceConsumer.as_asgi()),
    ]

    application = ProtocolTypeRouter({
        'websocket': TokenAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
    })

except ImportError:
    # channels not installed — routing is a no-op, HTTP still works via WSGI
    websocket_urlpatterns = []
    application = None
