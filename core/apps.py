from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Import the signals package — this registers all signal handlers:
        #   profile_signals, notification_signals, media_cleanup_signals
        import core.signals  # noqa: F401
