import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import StringIO
from threading import Barrier
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection, connections
from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from django_sonar import utils
from django_sonar.core.filters import PathFilter, SensitiveDataFilter
from django_sonar.core.collectors import DataCollector
from django_sonar.core.parsers import RequestParser
from django_sonar.logging import SonarHandler
from django_sonar.middlewares.requests import RequestsMiddleware
from django_sonar.models import SonarData, SonarRequest


class CaptureContextHardeningTests(TestCase):
    def test_helpers_ignore_data_outside_request_context(self):
        utils.sonar('ignored')
        utils.add_sonar_event({'name': 'ignored'})
        utils.add_sonar_log({'message': 'ignored'})
        utils.add_sonar_exception({'message': 'ignored'})

        self.assertEqual(utils.get_sonar_dump(), [])
        self.assertEqual(utils.get_sonar_events(), [])
        self.assertEqual(utils.get_sonar_logs(), [])
        self.assertEqual(utils.get_sonar_exceptions(), [])

    def test_contextvars_isolate_concurrent_capture(self):
        barrier = Barrier(2)

        def capture(value):
            token = utils.start_capture_context()
            try:
                utils.sonar(value)
                utils.add_sonar_event({'name': value})
                barrier.wait(timeout=5)
                return list(utils.get_sonar_dump()), list(utils.get_sonar_events())
            finally:
                utils.end_capture_context(token)

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(capture, ('first', 'second')))

        self.assertCountEqual(
            results,
            [(['first'], [{'name': 'first'}]), (['second'], [{'name': 'second'}])],
        )

    def test_sonar_handler_ignores_logs_outside_request(self):
        record = logging.LogRecord('test', logging.INFO, __file__, 1, 'ignored', (), None)
        SonarHandler().emit(record)
        self.assertEqual(utils.get_sonar_logs(), [])


class PrivacyHardeningTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_sensitive_filter_handles_root_lists_and_cookie(self):
        filtered = SensitiveDataFilter().filter([
            {'password': 'secret'},
            {'Cookie': 'sessionid=secret'},
            {'profile': {'api_key': 'secret'}},
        ])

        self.assertEqual(filtered[0]['password'], SensitiveDataFilter.MASK_VALUE)
        self.assertEqual(filtered[1]['Cookie'], SensitiveDataFilter.MASK_VALUE)
        self.assertEqual(filtered[2]['profile']['api_key'], SensitiveDataFilter.MASK_VALUE)

    def test_raw_body_is_disabled_by_default(self):
        request = self.factory.generic('POST', '/hook/', b'secret body', content_type='text/plain')
        payload = RequestParser.get_body_payload(request)

        self.assertNotIn('_raw_body', payload)
        self.assertFalse(payload['_raw_body_captured'])

    def test_raw_body_opt_in_respects_byte_limit(self):
        request = self.factory.generic('POST', '/hook/', b'abcdef', content_type='text/plain')
        payload = RequestParser.get_body_payload(
            request,
            capture_raw_body=True,
            raw_body_max_bytes=3,
        )

        self.assertEqual(payload['_raw_body'], 'abc... (truncated)')
        self.assertTrue(payload['_raw_body_truncated'])

    def test_json_root_list_is_sanitized_by_middleware(self):
        request = self.factory.generic(
            'POST',
            '/api/',
            b'[{"password": "secret"}]',
            content_type='application/json',
        )
        middleware = RequestsMiddleware(lambda _request: HttpResponse('OK'))
        middleware(request)

        payload = SonarData.objects.get(category='payload').data['post_payload']
        self.assertEqual(payload[0]['password'], SensitiveDataFilter.MASK_VALUE)


class MiddlewareHardeningTests(TestCase):
    databases = {'default', 'other'}

    def setUp(self):
        self.factory = RequestFactory()

    def test_settings_are_optional_and_missing_session_user_are_supported(self):
        middleware = RequestsMiddleware(lambda _request: HttpResponse('OK'))
        response = middleware(self.factory.get('/missing/'))

        self.assertEqual(response.status_code, 200)
        details = SonarData.objects.get(category='details').data
        self.assertIsNone(details['user_info'])
        self.assertEqual(details['view_func'], '<unresolved>')

    def test_persistence_failure_does_not_change_application_response(self):
        middleware = RequestsMiddleware(lambda _request: HttpResponse('original', status=202))
        with patch.object(middleware, '_persist_capture', side_effect=RuntimeError('offline')):
            with self.assertLogs('django_sonar.middlewares.requests', level='WARNING'):
                response = middleware(self.factory.get('/test/'))

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.content, b'original')
        self.assertFalse(utils.is_capture_active())

    def test_partial_persistence_is_rolled_back(self):
        middleware = RequestsMiddleware(lambda _request: HttpResponse('original'))
        with patch.object(DataCollector, 'save_payload', side_effect=RuntimeError('offline')):
            with self.assertLogs('django_sonar.middlewares.requests', level='WARNING'):
                response = middleware(self.factory.get('/test/'))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(SonarRequest.objects.exists())
        self.assertFalse(SonarData.objects.exists())

    def test_application_exception_cleans_capture_context(self):
        def failing_response(_request):
            utils.sonar('temporary')
            raise ValueError('application failure')

        middleware = RequestsMiddleware(failing_response)
        with self.assertRaisesMessage(ValueError, 'application failure'):
            middleware(self.factory.get('/test/'))

        self.assertFalse(utils.is_capture_active())
        self.assertEqual(utils.get_sonar_dump(), [])

    @override_settings(DEBUG=False, DJANGO_SONAR={'max_queries_per_request': 1})
    def test_queries_are_captured_and_limited_with_debug_disabled(self):
        user_model = get_user_model()

        def queried_response(_request):
            user_model.objects.exists()
            user_model.objects.count()
            return HttpResponse('OK')

        RequestsMiddleware(queried_response)(self.factory.get('/queries/'))

        sonar_request = SonarRequest.objects.get()
        query_data = SonarData.objects.get(category='queries').data
        self.assertEqual(sonar_request.query_count, 2)
        self.assertEqual(query_data['query_count'], 2)
        self.assertEqual(len(query_data['executed_queries']), 1)
        self.assertTrue(query_data['queries_truncated'])
        self.assertEqual(query_data['executed_queries'][0]['alias'], 'default')

    @override_settings(DJANGO_SONAR={'capture_memory': False})
    def test_memory_capture_can_be_disabled(self):
        RequestsMiddleware(lambda _request: HttpResponse('OK'))(self.factory.get('/test/'))
        details = SonarData.objects.get(category='details').data
        self.assertIsNone(details['memory_used'])

    @override_settings(DEBUG=False)
    def test_queries_are_captured_from_multiple_database_aliases(self):
        def queried_response(_request):
            with connections['default'].cursor() as cursor:
                cursor.execute('SELECT 1')
            with connections['other'].cursor() as cursor:
                cursor.execute('SELECT 1')
            return HttpResponse('OK')

        RequestsMiddleware(queried_response)(self.factory.get('/multi-db/'))

        query_data = SonarData.objects.get(category='queries').data
        aliases = {query['alias'] for query in query_data['executed_queries']}
        self.assertEqual(query_data['query_count'], 2)
        self.assertEqual(aliases, {'default', 'other'})


class ViewAndPaginationHardeningTests(TestCase):
    def setUp(self):
        self.client = Client()
        user_model = get_user_model()
        self.admin = user_model.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.client.force_login(self.admin)

    def test_missing_request_and_query_index_return_404(self):
        missing = self.client.get(
            reverse('sonar_request_detail', kwargs={'uuid': uuid4()}),
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(missing.status_code, 404)

        sonar_request = SonarRequest.objects.create(
            verb='GET', path='/', status='200', duration=1
        )
        SonarData.objects.create(
            sonar_request=sonar_request,
            category='queries',
            data={'executed_queries': []},
        )
        out_of_range = self.client.get(
            reverse('sonar_queries_detail', kwargs={'uuid': sonar_request.uuid, 'index': 0}),
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(out_of_range.status_code, 404)

    @override_settings(DJANGO_SONAR={'page_size': 2})
    def test_builtin_panels_are_paginated(self):
        sonar_request = SonarRequest.objects.create(
            verb='GET', path='/', status='200', duration=1
        )
        for index in range(3):
            SonarData.objects.create(
                sonar_request=sonar_request,
                category='events',
                data={'name': f'event-{index}'},
            )

        response = self.client.get(reverse('sonar_events'), {'page': 2}, HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['events']), 1)
        self.assertEqual(response.context['page_obj'].number, 2)


class ClearCommandHardeningTests(TestCase):
    databases = {'default', 'sonar_db'}

    def _request(self, path):
        return SonarRequest.objects.create(verb='GET', path=path, status='200', duration=1)

    def test_older_than_prunes_only_expired_requests(self):
        old = self._request('/old/')
        recent = self._request('/recent/')
        SonarRequest.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - timedelta(days=10)
        )
        SonarData.objects.create(sonar_request=old, category='events', data={})
        SonarData.objects.create(sonar_request=recent, category='events', data={})

        call_command('clear_sonar_data', no_input=True, older_than=5, stdout=StringIO())

        self.assertFalse(SonarRequest.objects.filter(pk=old.pk).exists())
        self.assertTrue(SonarRequest.objects.filter(pk=recent.pk).exists())
        self.assertEqual(SonarData.objects.count(), 1)

    def test_full_clear_rolls_back_and_raises_command_error(self):
        sonar_request = self._request('/kept/')
        SonarData.objects.create(sonar_request=sonar_request, category='events', data={})

        with patch.object(connection.ops, 'sequence_reset_sql', side_effect=RuntimeError('reset failed')):
            with self.assertRaises(CommandError):
                call_command('clear_sonar_data', no_input=True, stdout=StringIO())

        self.assertTrue(SonarRequest.objects.filter(pk=sonar_request.pk).exists())
        self.assertEqual(SonarData.objects.count(), 1)

    def test_invalid_retention_is_rejected(self):
        with self.assertRaises(CommandError):
            call_command('clear_sonar_data', no_input=True, older_than=0, stdout=StringIO())

    def test_explicit_database_alias_is_cleaned(self):
        sonar_request = SonarRequest.objects.using('sonar_db').create(
            verb='GET', path='/sonar-db/', status='200', duration=1
        )
        SonarData.objects.using('sonar_db').create(
            sonar_request=sonar_request,
            category='events',
            data={},
        )

        call_command(
            'clear_sonar_data',
            no_input=True,
            database='sonar_db',
            stdout=StringIO(),
        )

        self.assertFalse(SonarRequest.objects.using('sonar_db').exists())
        self.assertFalse(SonarData.objects.using('sonar_db').exists())

    @override_settings(
        DATABASE_ROUTERS=['django_sonar.db_router.SonarDatabaseRouter'],
    )
    def test_router_selected_database_alias_is_cleaned(self):
        sonar_request = SonarRequest.objects.using('sonar_db').create(
            verb='GET', path='/routed/', status='200', duration=1
        )
        SonarData.objects.using('sonar_db').create(
            sonar_request=sonar_request,
            category='events',
            data={},
        )

        call_command('clear_sonar_data', no_input=True, stdout=StringIO())

        self.assertFalse(SonarRequest.objects.using('sonar_db').exists())


class ModelIndexHardeningTests(TestCase):
    def test_expected_capture_indexes_are_declared(self):
        request_indexes = {index.name for index in SonarRequest._meta.indexes}
        data_indexes = {index.name for index in SonarData._meta.indexes}
        self.assertIn('sonar_req_created_idx', request_indexes)
        self.assertIn('sonar_data_cat_created_idx', data_indexes)

    def test_path_filter_defaults_to_no_exclusions(self):
        self.assertFalse(PathFilter().should_exclude('/anything/'))
