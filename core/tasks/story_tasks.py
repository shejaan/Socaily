"""
core/tasks/story_tasks.py
--------------------------
Celery tasks for story lifecycle management.
"""

import logging

logger = logging.getLogger(__name__)

# Lazy import: only import celery if it's installed
try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    def shared_task(func):
        """No-op decorator when Celery is not installed."""
        return func


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def expire_old_stories_task(self):
    """
    Periodic Celery task: delete stories older than 24 hours.
    Schedule with Celery Beat every hour.
    """
    try:
        from core.services.story_service import expire_old_stories
        deleted = expire_old_stories()
        logger.info("Story cleanup: deleted %d expired stories.", deleted)
        return {'deleted': deleted}
    except Exception as exc:
        logger.error("Story cleanup failed: %s", exc)
        raise self.retry(exc=exc)
