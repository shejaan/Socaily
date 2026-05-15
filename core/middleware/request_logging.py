"""
core/middleware/request_logging.py
------------------------------------
Structured request logging middleware.
Logs method, path, status code, and response time for non-static requests.
"""

import time
import logging

logger = logging.getLogger('core.requests')

# Skip logging for these path prefixes (static/media files, healthchecks)
SKIP_PREFIXES = ('/static/', '/media/', '/favicon.ico')


class RequestLoggingMiddleware:
    """
    Logs each request with: method, path, status_code, duration_ms.
    Skips static/media file paths to keep logs clean.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip logging for static / media
        if any(request.path.startswith(p) for p in SKIP_PREFIXES):
            return self.get_response(request)

        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000

        logger.info(
            "%s %s %s %.1fms",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response
