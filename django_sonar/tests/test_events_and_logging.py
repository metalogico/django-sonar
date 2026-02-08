"""
Tests for event helper API and logging handler integration.
"""

import logging

from django.test import TestCase

from django_sonar import utils
from django_sonar.events import sonar_event
from django_sonar.logging import SonarHandler


class EventAndLoggingHelpersTestCase(TestCase):
    """Validate event and logging helper buffering behavior."""

    def setUp(self):
        super().setUp()
        utils.reset_sonar_events()
        utils.reset_sonar_logs()

    def tearDown(self):
        utils.reset_sonar_events()
        utils.reset_sonar_logs()
        super().tearDown()

    def test_sonar_event_queues_structured_event(self):
        """sonar_event should queue name/level/payload/tags for collection."""
        event = sonar_event('cache.miss', payload={'key': 'users:1'}, level='warning', tags=['cache'])

        queued = utils.get_sonar_events()
        self.assertEqual(len(queued), 1)
        self.assertEqual(queued[0]['name'], 'cache.miss')
        self.assertEqual(queued[0]['level'], 'warning')
        self.assertEqual(queued[0]['payload']['key'], 'users:1')
        self.assertEqual(queued[0]['tags'], ['cache'])
        self.assertIn('timestamp', event)

    def test_sonar_logging_handler_queues_structured_log(self):
        """SonarHandler should queue structured log payload from LogRecord."""
        logger = logging.getLogger('django_sonar.tests.logger')
        handler = SonarHandler()

        original_handlers = list(logger.handlers)
        original_propagate = logger.propagate
        original_level = logger.level

        logger.handlers = [handler]
        logger.propagate = False
        logger.setLevel(logging.INFO)

        try:
            logger.info('background task complete', extra={'task_id': 'task-123'})
        finally:
            logger.handlers = original_handlers
            logger.propagate = original_propagate
            logger.setLevel(original_level)

        queued = utils.get_sonar_logs()
        self.assertEqual(len(queued), 1)
        self.assertEqual(queued[0]['logger'], 'django_sonar.tests.logger')
        self.assertEqual(queued[0]['level'], 'info')
        self.assertEqual(queued[0]['message'], 'background task complete')
        self.assertEqual(queued[0]['context']['task_id'], 'task-123')
        self.assertEqual(queued[0]['extra']['task_id'], 'task-123')
        self.assertIn('timestamp', queued[0])

    def test_sonar_logging_handler_merges_nested_context_payload(self):
        """Nested `context` extra should merge with other extra attributes."""
        logger = logging.getLogger('django_sonar.tests.logger.context')
        handler = SonarHandler()

        original_handlers = list(logger.handlers)
        original_propagate = logger.propagate
        original_level = logger.level

        logger.handlers = [handler]
        logger.propagate = False
        logger.setLevel(logging.INFO)

        try:
            logger.info(
                'job finished',
                extra={
                    'context': {'job_id': 'job-9', 'duration_ms': 42},
                    'queue': 'default',
                },
            )
        finally:
            logger.handlers = original_handlers
            logger.propagate = original_propagate
            logger.setLevel(original_level)

        queued = utils.get_sonar_logs()
        self.assertEqual(len(queued), 1)
        self.assertEqual(queued[0]['message'], 'job finished')
        self.assertEqual(queued[0]['context']['job_id'], 'job-9')
        self.assertEqual(queued[0]['context']['duration_ms'], 42)
        self.assertEqual(queued[0]['context']['queue'], 'default')
