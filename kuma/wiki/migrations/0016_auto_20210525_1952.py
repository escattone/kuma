# Generated by Django 2.2.21 on 2021-05-25 19:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0015_auto_20210430_1617'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='revisionakismetsubmission',
            name='revision',
        ),
        migrations.RemoveField(
            model_name='revisionakismetsubmission',
            name='sender',
        ),
        migrations.DeleteModel(
            name='DocumentSpamAttempt',
        ),
        migrations.DeleteModel(
            name='RevisionAkismetSubmission',
        ),
    ]
