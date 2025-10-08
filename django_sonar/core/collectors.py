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
        SonarData.objects.create(
            sonar_request_id=self.sonar_request_uuid,
            category='details',
            data=make_json_serializable(details)
        )

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
        SonarData.objects.create(
            sonar_request_id=self.sonar_request_uuid,
            category='payload',
            data=make_json_serializable(payload)
        )

    def save_queries(self, executed_queries):
        """
        Save database queries executed during request.
        
        :param executed_queries: List of query dictionaries from Django
        """
        queries = {
            'executed_queries': executed_queries,
            'query_count': len(executed_queries)
        }
        SonarData.objects.create(
            sonar_request_id=self.sonar_request_uuid,
            category='queries',
            data=make_json_serializable(queries)
        )

    def save_headers(self, request_headers):
        """
        Save request headers.
        
        :param request_headers: Dictionary with request headers
        """
        headers = {
            'request_headers': request_headers
        }
        SonarData.objects.create(
            sonar_request_id=self.sonar_request_uuid,
            category='headers',
            data=make_json_serializable(headers)
        )

    def save_session(self, session_data):
        """
        Save session data.
        
        :param session_data: Dictionary with session data
        """
        session = {
            'session_data': session_data
        }
        SonarData.objects.create(
            sonar_request_id=self.sonar_request_uuid,
            category='session',
            data=make_json_serializable(session)
        )

    def save_dumps(self):
        """
        Save sonar() dumps from thread local storage.
        
        Retrieves dumps from utils.get_sonar_dump() and resets them.
        """
        sonar_dumps = utils.get_sonar_dump()
        for dump in sonar_dumps:
            SonarData.objects.create(
                sonar_request_id=self.sonar_request_uuid,
                category='dumps',
                data=make_json_serializable(dump)
            )
        utils.reset_sonar_dump()

    def save_exceptions(self):
        """
        Save exception data from thread local storage.
        
        Retrieves exceptions from utils.get_sonar_exceptions() and resets them.
        """
        sonar_exceptions = utils.get_sonar_exceptions()
        for ex in sonar_exceptions:
            SonarData.objects.create(
                sonar_request_id=self.sonar_request_uuid,
                category='exception',
                data=make_json_serializable(ex)
            )
        utils.reset_sonar_exceptions()
