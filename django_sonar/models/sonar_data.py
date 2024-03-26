from django.db import models
from django.utils.translation import gettext_lazy as _


class SonarData(models.Model):
    sonar_request = models.ForeignKey('SonarRequest', on_delete=models.CASCADE, to_field='uuid', verbose_name=_('Request UUID'))
    category = models.CharField(max_length=255, verbose_name=_('Category'))
    data = models.JSONField(verbose_name=_('Data'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created'))

    def __str__(self):
        return f"Dump {self.id} for Request {self.sonar_request}"

    class Meta:
        app_label = 'django_sonar'
        db_table = 'sonar_data'
