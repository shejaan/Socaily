"""
core/utils/helpers.py
---------------------
General-purpose helper functions used across the codebase.
"""

import os
import uuid

from django.http import HttpRequest


def is_ajax(request: HttpRequest) -> bool:
    """Check if the request is an AJAX / XHR request."""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def get_avatar_url(user) -> str | None:
    """
    Safely return the profile image URL for a user.
    Returns None if the user has no profile or no image set.
    """
    try:
        if user.profile and user.profile.profile_image:
            return user.profile.profile_image.url
    except Exception:
        pass
    return None


def safe_filename(filename: str) -> str:
    """
    Generate a UUID-based filename while preserving the original extension.
    Prevents path traversal and name collisions.
    """
    ext = os.path.splitext(filename)[1].lower()
    return f"{uuid.uuid4().hex}{ext}"


def get_client_ip(request: HttpRequest) -> str:
    """Extract the real client IP, accounting for reverse proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def format_count(n: int) -> str:
    """Format large numbers: 1500 → '1.5k', 1000000 → '1M'."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".rstrip('0').rstrip('.')
    if n >= 1_000:
        return f"{n / 1_000:.1f}k".rstrip('0').rstrip('.')
    return str(n)


def paginate_queryset(queryset, page_number, per_page: int):
    """
    Thin wrapper around Django's Paginator.
    Returns a page object.
    """
    from django.core.paginator import Paginator
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page_number)
