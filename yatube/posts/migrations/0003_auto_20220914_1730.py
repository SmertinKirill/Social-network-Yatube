# Generated by Django 2.2.19 on 2022-09-14 17:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_auto_20220914_1721'),
    ]

    operations = [
        migrations.RenameField(
            model_name='group',
            old_name='text',
            new_name='description',
        ),
    ]
