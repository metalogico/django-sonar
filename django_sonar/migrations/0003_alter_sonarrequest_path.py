# Generated migration for changing path field from CharField to TextField

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_sonar', '0002_add_query_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sonarrequest',
            name='path',
            field=models.TextField(verbose_name='Path'),
        ),
    ]
