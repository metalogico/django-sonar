from django.core.management.base import BaseCommand
from django.db import transaction
from django_sonar.models import SonarRequest, SonarData


class Command(BaseCommand):
    help = 'Clear all DjangoSonar data from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Skip confirmation prompt'
        )

    def handle(self, *args, **options):
        if not options['no_input']:
            confirm = input(
                'This will permanently delete all DjangoSonar data. '
                'Are you sure? Type "yes" to continue: '
            )
            if confirm.lower() != 'yes':
                self.stdout.write('Operation cancelled.')
                return

        try:
            sonar_data_count = SonarData.objects.count()
            sonar_request_count = SonarRequest.objects.count()
            
            # Database-agnostic truncate using QuerySet methods
            SonarData.objects.all()._raw_delete(SonarData.objects.db)
            SonarRequest.objects.all()._raw_delete(SonarRequest.objects.db)
            
            # Reset sequences (PostgreSQL/MySQL)
            from django.core.management.color import no_style
            from django.db import connection
            
            style = no_style()
            sql = connection.ops.sql_flush(style, [SonarData._meta.db_table, SonarRequest._meta.db_table])
            with connection.cursor() as cursor:
                for query in sql:
                    cursor.execute(query)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully truncated {sonar_data_count} SonarData entries '
                    f'and {sonar_request_count} SonarRequest entries. IDs reset.'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error truncating tables: {e}')
            )