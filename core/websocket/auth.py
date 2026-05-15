"""
core/websocket/auth.py
-----------------------
WebSocket authentication middleware.
Wraps Django's session auth for Channels WebSocket connections.

Usage in routing.py:
    application = ProtocolTypeRouter({
        'websocket': TokenAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
    })
"""

try:
    from channels.middleware import BaseMiddleware
    from channels.auth import AuthMiddlewareStack
    from django.contrib.auth.models import AnonymousUser
    from django.db import close_old_connections

    class TokenAuthMiddleware(BaseMiddleware):
        """
        Authenticates WebSocket connections using Django session cookies.
        Falls back to AnonymousUser if no session found.

        For token-based auth (DRF Token / JWT), extend this class to
        extract the token from query params or headers.
        """

        async def __call__(self, scope, receive, send):
            close_old_connections()
            return await super().__call__(scope, receive, send)

    def TokenAuthMiddlewareStack(inner):
        """Convenience wrapper: sessions + token auth."""
        return AuthMiddlewareStack(TokenAuthMiddleware(inner))

except ImportError:
    # channels not installed
    def TokenAuthMiddlewareStack(inner):
        return inner
