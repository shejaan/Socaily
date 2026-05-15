"""
core/signals/__init__.py
-------------------------
Imports all signal modules so they are registered when CoreConfig.ready() fires.
"""

from core.signals import profile_signals       # noqa: F401
from core.signals import notification_signals  # noqa: F401
from core.signals import media_cleanup_signals # noqa: F401
