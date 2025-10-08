"""
Tests for the database router functionality.
"""

from django.test import TestCase
from django_sonar.db_router import SonarDatabaseRouter
from django_sonar.models import SonarRequest, SonarData


class SonarDatabaseRouterTestCase(TestCase):
    """Test case for the database router"""

    def setUp(self):
        """Set up test fixtures"""
        self.router = SonarDatabaseRouter()

    def test_db_for_read_sonar_models(self):
        """Test that sonar models are routed to sonar_db for reads"""
        self.assertEqual(
            self.router.db_for_read(SonarRequest),
            'sonar_db'
        )
        self.assertEqual(
            self.router.db_for_read(SonarData),
            'sonar_db'
        )

    def test_db_for_write_sonar_models(self):
        """Test that sonar models are routed to sonar_db for writes"""
        self.assertEqual(
            self.router.db_for_write(SonarRequest),
            'sonar_db'
        )
        self.assertEqual(
            self.router.db_for_write(SonarData),
            'sonar_db'
        )

    def test_allow_relation_sonar_models(self):
        """Test that relations between sonar models are allowed"""
        sonar_request = SonarRequest(
            verb='GET',
            path='/test/',
            status='200',
            duration=100,
        )
        sonar_data = SonarData(
            sonar_request=sonar_request,
            category='test',
            data={'test': 'data'}
        )
        
        self.assertTrue(
            self.router.allow_relation(sonar_request, sonar_data)
        )

    def test_allow_migrate_sonar_db(self):
        """Test that migrations are only allowed on sonar_db"""
        # Should allow migration on sonar_db
        self.assertTrue(
            self.router.allow_migrate('sonar_db', 'django_sonar')
        )
        
        # Should not allow migration on default db
        self.assertFalse(
            self.router.allow_migrate('default', 'django_sonar')
        )

    def test_allow_migrate_other_apps_on_default(self):
        """Test that other apps can migrate on default db"""
        # Router should return None for other apps on default, letting Django decide
        self.assertIsNone(
            self.router.allow_migrate('default', 'auth')
        )
        self.assertIsNone(
            self.router.allow_migrate('default', 'contenttypes')
        )

    def test_prevent_other_apps_on_sonar_db(self):
        """Test that other apps cannot migrate to sonar_db"""
        # Router should explicitly prevent other apps from migrating to sonar_db
        self.assertFalse(
            self.router.allow_migrate('sonar_db', 'auth')
        )
        self.assertFalse(
            self.router.allow_migrate('sonar_db', 'contenttypes')
        )
        self.assertFalse(
            self.router.allow_migrate('sonar_db', 'sessions')
        )
