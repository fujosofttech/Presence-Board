from django.apps import AppConfig


class PresenceConfig(AppConfig):
    name = 'apps.presence'

    def ready(self):
        import apps.presence.signals  # noqa: F401
