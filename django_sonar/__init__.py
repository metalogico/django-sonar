from django_sonar.events import sonar_event

__all__ = ["default_app_config", "APP_NAME", "VERSION", "sonar_event"]

default_app_config = 'django_sonar.apps.DjangoSonarConfig'
APP_NAME = "django_sonar"
VERSION = "0.5.0"
