"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Get standard Django ASGI application first
django_asgi_app = get_asgi_application()

try:
    from channels.routing import ProtocolTypeRouter, URLRouter
    from core.websocket.auth import TokenAuthMiddlewareStack
    from core.websocket.routing import websocket_urlpatterns

    application = ProtocolTypeRouter({
        "http": django_asgi_app,
        "websocket": TokenAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
    })
except ImportError:
    # Fallback to pure WSGI/ASGI if channels is not installed
    application = django_asgi_app
