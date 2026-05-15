"""
core/tasks/cleanup_tasks.py
-----------------------------
Celery tasks for cleaning up orphaned media files and stale data.
"""

import logging

logger = logging.getLogger(__name__)

try:
    from celery import shared_task
except ImportError:
    def shared_task(func):
        return func


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def cleanup_orphan_notifications(self):
    """
    Remove notifications where the associated post no longer exists.
    Runs periodically to keep the notifications table clean.
    """
    try:
        from core.models import Notification
        deleted, _ = (
            Notification.objects
            .filter(notif_type__in=['like', 'comment'], post__isnull=True)
            .delete()
        )
        logger.info("Notification cleanup: deleted %d orphan notifications.", deleted)
        return {'deleted': deleted}
    except Exception as exc:
        logger.error("Notification cleanup failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task
def cleanup_unread_old_notifications():
    """
    Mark notifications older than 30 days as read to keep unread counts accurate.
    """
    from datetime import timedelta
    from django.utils import timezone
    from core.models import Notification

    cutoff = timezone.now() - timedelta(days=30)
    updated = Notification.objects.filter(
        is_read=False, created_at__lt=cutoff
    ).update(is_read=True)

    logger.info("Marked %d old notifications as read.", updated)
    return {'updated': updated}
