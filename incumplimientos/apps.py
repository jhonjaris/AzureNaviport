from django.apps import AppConfig


class IncumplimientosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'incumplimientos'

    def ready(self):
        import incumplimientos.signals  # noqa
