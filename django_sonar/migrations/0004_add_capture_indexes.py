from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('django_sonar', '0003_alter_sonarrequest_path'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='sonarrequest',
            index=models.Index(fields=['-created_at'], name='sonar_req_created_idx'),
        ),
        migrations.AddIndex(
            model_name='sonarrequest',
            index=models.Index(fields=['verb', '-created_at'], name='sonar_req_verb_created_idx'),
        ),
        migrations.AddIndex(
            model_name='sonarrequest',
            index=models.Index(fields=['status', '-created_at'], name='sonar_req_stat_created_idx'),
        ),
        migrations.AddIndex(
            model_name='sonardata',
            index=models.Index(fields=['category', '-created_at'], name='sonar_data_cat_created_idx'),
        ),
        migrations.AddIndex(
            model_name='sonardata',
            index=models.Index(fields=['sonar_request', 'category'], name='sonar_data_req_cat_idx'),
        ),
    ]
