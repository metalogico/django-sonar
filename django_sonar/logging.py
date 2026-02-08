import logging

from django.utils import timezone

from django_sonar import utils
from django_sonar.utils import make_json_serializable


_DEFAULT_RECORD_KEYS = {
    'args',
    'asctime',
    'created',
    'exc_info',
    'exc_text',
    'filename',
    'funcName',
    'levelname',
    'levelno',
    'lineno',
    'module',
    'msecs',
    'message',
    'msg',
    'name',
    'pathname',
    'process',
    'processName',
    'relativeCreated',
    'stack_info',
    'thread',
    'threadName',
}


class SonarHandler(logging.Handler):
    """Capture Python log records into Sonar request-scoped storage."""

    def emit(self, record):
        try:
            message = self.format(record) if self.formatter else record.getMessage()
            context = self._extract_context(record)
            log_entry = {
                'logger': record.name,
                'level': record.levelname.lower(),
                'message': message,
                'context': context,
                # Keep backward compatibility for dashboards expecting `extra`.
                'extra': context,
                'timestamp': timezone.now().isoformat(),
            }
            utils.add_sonar_log(make_json_serializable(log_entry))
        except Exception:
            self.handleError(record)

    def _extract_context(self, record):
        context = {}
        for key, value in record.__dict__.items():
            if key in _DEFAULT_RECORD_KEYS:
                continue

            if key == 'context':
                if isinstance(value, dict):
                    context.update(value)
                else:
                    context['context'] = value
                continue

            context[key] = value

        return context
