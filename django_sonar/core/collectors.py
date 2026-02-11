"""
Data collection and persistence utilities.

Handles saving request data to SonarData model with different categories:
- details (user info, view function, memory usage)
- payload (GET/POST data)
- queries (database queries)
- headers (request headers)
- session (session data)
- dumps (sonar() dumps)
- exceptions (exception data)
"""

from django_sonar.models import SonarData
from django_sonar import utils
from django_sonar.utils import make_json_serializable


class DataCollector:
    """Handles collection and persistence of request data"""

    def __init__(self, sonar_request_uuid):
        """
        Initialize collector with request UUID.
        
        :param sonar_request_uuid: UUID of the SonarRequest instance
        """
        self.sonar_request_uuid = sonar_request_uuid

    def save_entry(self, category, payload, request_uuid=None, tags=None, meta=None):
        """
        Save a generic SonarData entry for any category.

        :param category: Entry category key
        :param payload: JSON-serializable payload body
        :param request_uuid: Optional SonarRequest UUID override
        :param tags: Optional list of tags
        :param meta: Optional metadata dictionary
        """
        target_request_uuid = request_uuid or self.sonar_request_uuid
        if not target_request_uuid:
            raise ValueError('A request UUID is required to save a sonar entry.')

        data = payload
        if tags is not None or meta is not None:
            data = {'payload': payload}
            if tags is not None:
                data['tags'] = tags
            if meta is not None:
                data['meta'] = meta

        SonarData.objects.create(
            sonar_request_id=target_request_uuid,
            category=category,
            data=make_json_serializable(data)
        )

    def save_details(self, user_info, view_func, middlewares_used, memory_diff):
        """
        Save request details (user, view, memory, middlewares).
        
        :param user_info: Dictionary with user information or None
        :param view_func: String identifying the view function
        :param middlewares_used: List/tuple of middleware names
        :param memory_diff: Memory usage in MB
        """
        details = {
            'user_info': user_info,
            'view_func': view_func,
            'middlewares_used': middlewares_used,
            'memory_used': memory_diff
        }
        self.save_entry('details', details)

    def save_payload(self, get_payload, post_payload):
        """
        Save request payload (GET and POST/body data).
        
        :param get_payload: Dictionary with GET parameters
        :param post_payload: Dictionary with POST/body data
        """
        payload = {
            'get_payload': get_payload,
            'post_payload': post_payload
        }
        self.save_entry('payload', payload)

    def save_queries(self, executed_queries):
        """
        Save database queries executed during request.
        
        :param executed_queries: List of query dictionaries from Django
        """
        queries = {
            'executed_queries': executed_queries,
            'query_count': len(executed_queries)
        }
        self.save_entry('queries', queries)

    def save_headers(self, request_headers):
        """
        Save request headers.
        
        :param request_headers: Dictionary with request headers
        """
        headers = {
            'request_headers': request_headers
        }
        self.save_entry('headers', headers)

    def save_session(self, session_data):
        """
        Save session data.
        
        :param session_data: Dictionary with session data
        """
        session = {
            'session_data': session_data
        }
        self.save_entry('session', session)

    def save_dumps(self):
        """
        Save sonar() dumps from thread local storage.
        
        Retrieves dumps from utils.get_sonar_dump() and resets them.
        """
        sonar_dumps = utils.get_sonar_dump()
        for dump in sonar_dumps:
            self.save_entry('dumps', dump)
        utils.reset_sonar_dump()

    def save_exceptions(self):
        """
        Save exception data from thread local storage.
        
        Retrieves exceptions from utils.get_sonar_exceptions() and resets them.
        """
        sonar_exceptions = utils.get_sonar_exceptions()
        for ex in sonar_exceptions:
            self.save_entry('exception', ex)
        utils.reset_sonar_exceptions()

    def save_events(self):
        """
        Save structured events from thread local storage.

        Retrieves events from utils.get_sonar_events() and resets them.
        """
        sonar_events = utils.get_sonar_events()
        for event in sonar_events:
            self.save_entry('events', event)
        utils.reset_sonar_events()

    def save_logs(self):
        """
        Save structured log entries from thread local storage.

        Retrieves logs from utils.get_sonar_logs() and resets them.
        """
        sonar_logs = utils.get_sonar_logs()
        for log_entry in sonar_logs:
            self.save_entry('logs', log_entry)
        utils.reset_sonar_logs()
