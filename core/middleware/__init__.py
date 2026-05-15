"""
core/middleware/__init__.py
----------------------------
Re-exports all middleware classes so settings.py can use the old
`core.middleware.AdminDebugMiddleware` path OR the new modular path.

Backward-compatible: `core.middleware.AdminDebugMiddleware` still works.
"""

from core.middleware.admin_debug      import AdminDebugMiddleware
from core.middleware.active_user      import ActiveUserMiddleware
from core.middleware.request_logging  import RequestLoggingMiddleware

__all__ = [
    'AdminDebugMiddleware',
    'ActiveUserMiddleware',
    'RequestLoggingMiddleware',
]
