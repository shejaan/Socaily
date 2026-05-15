"""
core/middleware/active_user.py
-------------------------------
Tracks the last-seen timestamp of authenticated users.
Stores the value in the Django cache so it's fast and doesn't
hit the DB on every request.
"""

from django.utils import timezone
from django.core.cache import cache

# How often (seconds) we actually write to cache — avoids hammering cache on every request
LAST_SEEN_UPDATE_INTERVAL = 60  # 1 minute


class ActiveUserMiddleware:
    """
    Updates a 'last_seen_{user_id}' cache key for authenticated users.
    Only writes once per LAST_SEEN_UPDATE_INTERVAL to avoid excessive cache writes.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            cache_key = f'last_seen_{request.user.id}'
            last_seen = cache.get(cache_key)

            if last_seen is None:
                cache.set(cache_key, timezone.now(), timeout=LAST_SEEN_UPDATE_INTERVAL * 2)

        return response
