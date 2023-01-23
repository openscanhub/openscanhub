# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import kobo.django.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Capability',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('function', models.CharField(max_length=128)),
                ('options', kobo.django.fields.JSONField(default={}, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ScanningSession',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('description', models.CharField(max_length=128, null=True, blank=True)),
                ('options', kobo.django.fields.JSONField(default={}, blank=True)),
                ('caps', models.ManyToManyField(to='errata.Capability')),
            ],
        ),
    ]
