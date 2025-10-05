"""
Django Sonar Test Suite

Organized test modules for comprehensive coverage of django-sonar functionality.
"""

# Middleware tests
from .test_middleware_basic import MiddlewareBasicTestCase
from .test_middleware_requests import MiddlewareRequestTypesTestCase
from .test_middleware_data_capture import MiddlewareDataCaptureTestCase
from .test_middleware_exclusions import MiddlewareExclusionsTestCase
from .test_middleware_helpers import MiddlewareHelpersTestCase

# Core module tests
from .test_core_parsers import RequestParserTestCase
from .test_core_filters import PathFilterTestCase
from .test_core_collectors import DataCollectorTestCase

__all__ = [
    # Middleware tests
    'MiddlewareBasicTestCase',
    'MiddlewareRequestTypesTestCase',
    'MiddlewareDataCaptureTestCase',
    'MiddlewareExclusionsTestCase',
    'MiddlewareHelpersTestCase',
    # Core tests
    'RequestParserTestCase',
    'PathFilterTestCase',
    'DataCollectorTestCase',
]
