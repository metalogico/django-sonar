import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class SonarRequest(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    verb = models.CharField(max_length=255, verbose_name=_('Verb'))
    path = models.TextField(verbose_name=_('Path'))
    status = models.CharField(max_length=255, verbose_name=_('Status'))
    duration = models.IntegerField(verbose_name=_('Duration'))
    query_count = models.IntegerField(verbose_name=_('Query Count'), default=0)
    ip_address = models.GenericIPAddressField(verbose_name=_('IP Address'), blank=True, null=True)
    hostname = models.CharField(max_length=255, verbose_name=_('Hostname'), blank=True, null=True)
    is_ajax = models.BooleanField(verbose_name=_('Ajax'), default=False)
    is_read = models.BooleanField(verbose_name=_('Read'), default=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created'))

    def __str__(self):
        return str(self.uuid)

    class Meta:
        app_label = 'django_sonar'
        db_table = 'sonar_requests'
