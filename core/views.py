"""
views.py – COMPATIBILITY SHIM
------------------------------
The views have been refactored into a package at core/views/.
This file is kept so that any direct `from core.views import X` references
(outside of urls.py) continue to work without changes.

DO NOT add logic here — add it to the appropriate module inside core/views/.
"""

# Re-export everything from the views package
from core.views import *  # noqa: F401, F403
