# Generated by Django 5.1.4 on 2025-01-12 05:09

import ckeditor.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scores', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='content',
        ),
        migrations.AlterField(
            model_name='activity',
            name='description',
            field=ckeditor.fields.RichTextField(),
        ),
    ]
