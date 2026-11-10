from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import DEFAULT_DB_ALIAS, connections, router, transaction
from django.utils import timezone

from django_sonar.models import SonarData, SonarRequest


class Command(BaseCommand):
    help = 'Clear all Django Sonar data or prune records older than a number of days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Skip confirmation prompt',
        )
        parser.add_argument(
            '--database',
            help='Database alias to clean; defaults to the alias selected by the router',
        )
        parser.add_argument(
            '--older-than',
            type=int,
            metavar='DAYS',
            help='Delete only requests older than this many days',
        )

    def handle(self, *args, **options):
        older_than = options['older_than']
        if older_than is not None and older_than < 1:
            raise CommandError('--older-than must be a positive number of days.')

        database_alias = (
            options['database']
            or router.db_for_write(SonarRequest)
            or DEFAULT_DB_ALIAS
        )
        if database_alias not in connections:
            raise CommandError(f'Unknown database alias: {database_alias}')

        requests = SonarRequest.objects.using(database_alias).all()
        description = 'all Django Sonar data'
        if older_than is not None:
            cutoff = timezone.now() - timedelta(days=older_than)
            requests = requests.filter(created_at__lt=cutoff)
            description = f'Django Sonar data older than {older_than} day(s)'

        if not options['no_input']:
            confirm = input(
                f'This will permanently delete {description} from "{database_alias}". '
                'Are you sure? Type "yes" to continue: '
            )
            if confirm.lower() != 'yes':
                self.stdout.write('Operation cancelled.')
                return

        try:
            request_count = requests.count()
            data_count = SonarData.objects.using(database_alias).filter(
                sonar_request_id__in=requests.values('uuid')
            ).count()

            with transaction.atomic(using=database_alias):
                requests.delete()
                if older_than is None:
                    connection = connections[database_alias]
                    reset_sql = connection.ops.sequence_reset_sql(
                        no_style(), [SonarData, SonarRequest]
                    )
                    with connection.cursor() as cursor:
                        for query in reset_sql:
                            cursor.execute(query)
        except Exception as exc:
            raise CommandError(
                f'Unable to clear Django Sonar data from "{database_alias}": {exc}'
            ) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f'Deleted {data_count} SonarData entries and '
                f'{request_count} SonarRequest entries from "{database_alias}".'
            )
        )
