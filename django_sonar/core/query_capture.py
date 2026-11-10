"""Database query capture that also works when Django DEBUG is disabled."""

from contextlib import ExitStack, contextmanager
import sys
from time import perf_counter

from django.db import connections


class QueryCapture:
    """Collect query count and a bounded set of rendered query details."""

    def __init__(self, max_queries):
        self.max_queries = max(0, int(max_queries))
        self.queries = []
        self.query_count = 0
        self.setup_error = None

    @property
    def truncated(self):
        return self.query_count > len(self.queries)

    def wrapper_for(self, connection):
        alias = connection.alias

        def capture(execute, sql, params, many, context):
            started_at = perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                elapsed = perf_counter() - started_at
                self.query_count += 1
                if len(self.queries) < self.max_queries:
                    try:
                        rendered_sql = connection.ops.last_executed_query(
                            context['cursor'], sql, params
                        )
                    except Exception:
                        rendered_sql = str(sql)
                    self.queries.append({
                        'sql': rendered_sql,
                        'time': f'{elapsed:.3f}',
                        'alias': alias,
                    })

        return capture


@contextmanager
def capture_database_queries(max_queries):
    """Install request-local execute wrappers on every configured database."""
    capture = QueryCapture(max_queries)
    stack = ExitStack()
    try:
        for connection in connections.all():
            stack.enter_context(connection.execute_wrapper(capture.wrapper_for(connection)))
    except Exception:
        capture.setup_error = sys.exc_info()
        stack.close()
        yield capture
    else:
        with stack:
            yield capture
