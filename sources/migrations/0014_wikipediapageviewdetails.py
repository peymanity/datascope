# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import json_field.fields
import core.utils.configuration


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('sources', '0013_imagefeatures'),
    ]

    operations = [
        migrations.CreateModel(
            name='WikipediaPageviewDetails',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('uri', models.CharField(db_index=True, max_length=255, default=None)),
                ('data_hash', models.CharField(db_index=True, max_length=255, default='')),
                ('config', core.utils.configuration.ConfigurationField()),
                ('request', json_field.fields.JSONField(help_text='Enter a valid JSON object', default=None)),
                ('head', json_field.fields.JSONField(help_text='Enter a valid JSON object', default=None)),
                ('body', models.TextField(default=None)),
                ('status', models.PositiveIntegerField(default=None)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('purge_at', models.DateTimeField(null=True, blank=True)),
                ('retainer_id', models.PositiveIntegerField(null=True)),
                ('retainer_type', models.ForeignKey(to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
