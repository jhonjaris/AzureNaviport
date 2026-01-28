from django.apps import AppConfig


class SolicitudesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'solicitudes'

    def ready(self):
        """Importar signals cuando la app esté lista"""
        import solicitudes.signals  # noqa
