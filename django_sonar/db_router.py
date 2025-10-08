"""
Database router for Django Sonar to use a separate database.

This allows storing monitoring/debugging data in a separate database
to avoid impacting your main application's performance.
"""


class SonarDatabaseRouter:
    """
    A router to control all database operations on models in the
    django_sonar application.
    """
    
    route_app_labels = {'django_sonar'}
    
    def db_for_read(self, model, **hints):
        """
        Attempts to read django_sonar models go to sonar_db.
        """
        if model._meta.app_label in self.route_app_labels:
            return 'sonar_db'
        return None
    
    def db_for_write(self, model, **hints):
        """
        Attempts to write django_sonar models go to sonar_db.
        """
        if model._meta.app_label in self.route_app_labels:
            return 'sonar_db'
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the django_sonar app is involved.
        """
        if (
            obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the django_sonar app only appears in the 'sonar_db'
        database, and other apps don't appear in 'sonar_db'.
        """
        if app_label in self.route_app_labels:
            # Only allow django_sonar migrations on sonar_db
            return db == 'sonar_db'
        elif db == 'sonar_db':
            # Don't allow non-sonar apps to migrate to sonar_db
            return False
        # For other cases, let other routers or Django decide
        return None
