"""
Tests for JSON serialization of non-standard Python types.
"""

import json
from decimal import Decimal
from datetime import datetime, date, time
from uuid import UUID, uuid4
from django.test import TestCase
from django_sonar.utils import make_json_serializable, sonar, get_sonar_dump, reset_sonar_dump


class JSONSerializationTestCase(TestCase):
    """Test case for JSON serialization utilities"""

    def setUp(self):
        """Set up test fixtures"""
        reset_sonar_dump()

    def test_decimal_serialization(self):
        """Test that Decimal objects are converted to float"""
        data = {'price': Decimal('19.99')}
        result = make_json_serializable(data)
        self.assertEqual(result['price'], 19.99)
        self.assertIsInstance(result['price'], float)
        # Verify it's actually JSON serializable
        json.dumps(result)

    def test_datetime_serialization(self):
        """Test that datetime objects are converted to ISO format string"""
        now = datetime(2024, 1, 15, 12, 30, 45)
        data = {'timestamp': now}
        result = make_json_serializable(data)
        self.assertEqual(result['timestamp'], '2024-01-15T12:30:45')
        self.assertIsInstance(result['timestamp'], str)
        json.dumps(result)

    def test_date_serialization(self):
        """Test that date objects are converted to ISO format string"""
        today = date(2024, 1, 15)
        data = {'date': today}
        result = make_json_serializable(data)
        self.assertEqual(result['date'], '2024-01-15')
        self.assertIsInstance(result['date'], str)
        json.dumps(result)

    def test_time_serialization(self):
        """Test that time objects are converted to ISO format string"""
        t = time(12, 30, 45)
        data = {'time': t}
        result = make_json_serializable(data)
        self.assertEqual(result['time'], '12:30:45')
        self.assertIsInstance(result['time'], str)
        json.dumps(result)

    def test_uuid_serialization(self):
        """Test that UUID objects are converted to string"""
        uid = uuid4()
        data = {'id': uid}
        result = make_json_serializable(data)
        self.assertEqual(result['id'], str(uid))
        self.assertIsInstance(result['id'], str)
        json.dumps(result)

    def test_bytes_serialization(self):
        """Test that bytes objects are decoded to string"""
        data = {'data': b'hello'}
        result = make_json_serializable(data)
        self.assertEqual(result['data'], 'hello')
        self.assertIsInstance(result['data'], str)
        json.dumps(result)

    def test_set_serialization(self):
        """Test that set objects are converted to list"""
        data = {'tags': {1, 2, 3}}
        result = make_json_serializable(data)
        self.assertIsInstance(result['tags'], list)
        self.assertEqual(set(result['tags']), {1, 2, 3})
        json.dumps(result)

    def test_nested_structure_serialization(self):
        """Test that nested structures with mixed types are handled"""
        data = {
            'user': {
                'id': uuid4(),
                'balance': Decimal('100.50'),
                'created_at': datetime(2024, 1, 1, 10, 0, 0),
            },
            'items': [
                {'price': Decimal('19.99'), 'quantity': 2},
                {'price': Decimal('29.99'), 'quantity': 1},
            ],
            'tags': {'electronics', 'sale'},
        }
        result = make_json_serializable(data)
        
        # Verify nested UUID
        self.assertIsInstance(result['user']['id'], str)
        
        # Verify nested Decimal
        self.assertIsInstance(result['user']['balance'], float)
        self.assertEqual(result['user']['balance'], 100.50)
        
        # Verify nested datetime
        self.assertIsInstance(result['user']['created_at'], str)
        
        # Verify list of dicts with Decimals
        self.assertIsInstance(result['items'][0]['price'], float)
        
        # Verify set conversion
        self.assertIsInstance(result['tags'], list)
        
        # Verify final result is JSON serializable
        json.dumps(result)

    def test_sonar_with_decimal(self):
        """Test that sonar() function handles Decimal correctly"""
        data = {'price': Decimal('19.99')}
        sonar(data)
        
        dumps = get_sonar_dump()
        self.assertEqual(len(dumps), 1)
        self.assertEqual(dumps[0]['price'], 19.99)
        
        # Verify stored data is JSON serializable
        json.dumps(dumps[0])

    def test_sonar_with_complex_types(self):
        """Test that sonar() function handles multiple complex types"""
        data = {
            'id': uuid4(),
            'price': Decimal('99.99'),
            'timestamp': datetime.now(),
            'date': date.today(),
        }
        sonar(data)
        
        dumps = get_sonar_dump()
        self.assertEqual(len(dumps), 1)
        
        # Verify all types were converted
        self.assertIsInstance(dumps[0]['id'], str)
        self.assertIsInstance(dumps[0]['price'], float)
        self.assertIsInstance(dumps[0]['timestamp'], str)
        self.assertIsInstance(dumps[0]['date'], str)
        
        # Verify stored data is JSON serializable
        json.dumps(dumps[0])

    def test_primitive_types_unchanged(self):
        """Test that primitive types are not modified"""
        data = {
            'string': 'hello',
            'integer': 42,
            'float': 3.14,
            'boolean': True,
            'none': None,
        }
        result = make_json_serializable(data)
        
        self.assertEqual(result, data)
        self.assertIsInstance(result['string'], str)
        self.assertIsInstance(result['integer'], int)
        self.assertIsInstance(result['float'], float)
        self.assertIsInstance(result['boolean'], bool)
        self.assertIsNone(result['none'])

    def test_custom_object_serialization(self):
        """Test that custom objects are converted to string representation"""
        class CustomObject:
            def __str__(self):
                return "custom_value"
        
        data = {'obj': CustomObject()}
        result = make_json_serializable(data)
        
        self.assertEqual(result['obj'], 'custom_value')
        self.assertIsInstance(result['obj'], str)
        json.dumps(result)

    def tearDown(self):
        """Clean up after tests"""
        reset_sonar_dump()
