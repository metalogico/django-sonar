# Generated migration for adding query_count field

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('django_sonar', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sonarrequest',
            name='query_count',
            field=models.IntegerField(default=0, verbose_name='Query Count'),
        ),
    ]
