# Django Sonar Test Suite

Organized test modules for comprehensive coverage of django-sonar functionality.

## Structure

```
tests/
├── __init__.py                          # Test suite exports
├── base.py                              # Base test case with common setup
│
├── test_middleware_basic.py             # Basic middleware functionality
├── test_middleware_requests.py          # HTTP request types (GET, POST, PUT, etc.)
├── test_middleware_data_capture.py      # Data capture (headers, sessions, user info)
├── test_middleware_exclusions.py        # Path exclusion patterns
├── test_middleware_helpers.py           # Helper methods
│
├── test_core_parsers.py                 # RequestParser class tests
├── test_core_filters.py                 # PathFilter class tests
└── test_core_collectors.py              # DataCollector class tests
```

## Running Tests

### Run all tests
```bash
python manage.py test django_sonar
```

### Run specific test module
```bash
python manage.py test django_sonar.tests.test_middleware_basic
python manage.py test django_sonar.tests.test_middleware_requests
python manage.py test django_sonar.tests.test_middleware_data_capture
python manage.py test django_sonar.tests.test_middleware_exclusions
python manage.py test django_sonar.tests.test_middleware_helpers
```

### Run specific test case
```bash
python manage.py test django_sonar.tests.MiddlewareBasicTestCase
```

### Run specific test method
```bash
python manage.py test django_sonar.tests.test_middleware_basic.MiddlewareBasicTestCase.test_middleware_basic_get_request
```

### Run with verbosity
```bash
python manage.py test django_sonar -v 2
```

## Test Coverage

### test_middleware_basic.py (4 tests)
- Basic GET request processing
- Request duration capture
- Hostname capture
- UUID persistence across SonarRequest and SonarData

### test_middleware_requests.py (10 tests)
- POST requests with form data (standard and extended)
- GET requests with query strings
- PUT requests with JSON
- PATCH requests with form-encoded data
- DELETE requests
- AJAX request detection
- Invalid JSON handling
- Different HTTP status codes

### test_middleware_data_capture.py (11 tests)
- Authenticated user information
- Anonymous user handling
- Request headers capture
- Session data capture
- IP address capture (REMOTE_ADDR and X-Forwarded-For)
- Memory usage tracking
- View function identification
- Middlewares list capture
- Sonar dump integration
- Exception handling

### test_middleware_exclusions.py (4 tests)
- Literal path exclusions
- Regex path exclusions
- Mixed literal and regex patterns
- Empty exclusions list

### test_middleware_helpers.py (2 tests)
- process_exception() stores exception info
- process_exception() captures traceback

### test_core_parsers.py (10 tests)
- get_client_ip() with X-Forwarded-For
- get_client_ip() with REMOTE_ADDR only
- is_ajax() detection
- get_body_payload() for GET requests
- get_body_payload() for POST requests
- get_body_payload() with JSON data
- get_body_payload() with form-encoded data
- get_body_payload() with invalid JSON

### test_core_filters.py (5 tests)
- Literal path exclusions
- Regex path exclusions
- Mixed literal and regex patterns
- Empty exclusions list
- Invalid regex fallback to literal

### test_core_collectors.py (9 tests)
- save_details() method
- save_payload() method
- save_queries() method
- save_headers() method
- save_session() method
- save_dumps() integration with utils
- save_exceptions() integration with utils
- Multiple request handling

## Total Coverage
**54 tests** covering middleware and core modules

## Common Issues & Design Decisions

### DJANGO_SONAR Setting
All tests that instantiate `RequestsMiddleware` need the `@override_settings(DJANGO_SONAR={'excludes': []})` decorator because the middleware reads this setting during initialization.

### URL Resolution
Tests use a mocked `resolve()` function (configured in `base.py`) to avoid dependency on actual URL patterns. This allows testing the middleware in isolation.

### Multipart Form Data
Testing multipart/form-data uploads with `RequestFactory` is complex due to Django's upload handler system. The middleware handles multipart data correctly in production; unit tests focus on standard POST data and JSON payloads.
