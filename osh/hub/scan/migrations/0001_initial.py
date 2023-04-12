# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import kobo.django.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hub', '0003_auto_20160202_0647'),
    ]

    operations = [
        migrations.CreateModel(
            name='Analyzer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='AnalyzerVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('version', models.CharField(max_length=64)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'get_latest_by': 'date_created',
            },
        ),
        migrations.CreateModel(
            name='AppSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=128)),
                ('value', models.TextField(null=True, blank=True)),
            ],
            options={
                'verbose_name_plural': 'AppSettings',
            },
        ),
        migrations.CreateModel(
            name='ClientAnalyzer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('version', models.CharField(max_length=32, null=True, blank=True)),
                ('enabled', models.BooleanField(default=True)),
                ('cli_short_command', models.CharField(max_length=32, null=True, blank=True)),
                ('cli_long_command', models.CharField(max_length=32)),
                ('build_append', models.CharField(help_text=b'analyzer name to put in --tools', max_length=32, null=True, blank=True)),
                ('build_append_args', models.CharField(max_length=256, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ETMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('advisory_id', models.CharField(max_length=16)),
                ('et_scan_id', models.CharField(max_length=16)),
                ('comment', models.CharField(default=b'', max_length=256, blank=True)),
                ('state', models.PositiveIntegerField(default=0, help_text=b'Status of request', choices=[(0, b'OK'), (1, b'ERROR'), (2, b'INELIGIBLE')])),
            ],
        ),
        migrations.CreateModel(
            name='MockConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=256)),
                ('enabled', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name=b'Package name')),
                ('blocked', models.NullBooleanField(default=False, help_text=b'If this is set to True, the package is blocked -- not accepted for scanning.')),
                ('eligible', models.NullBooleanField(default=True, help_text=b'DEPRECATED, do not use; use package attribute instead.')),
            ],
        ),
        migrations.CreateModel(
            name='PackageAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=64, null=True, blank=True)),
                ('value', models.CharField(max_length=128, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='PackageCapability',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_capable', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Permissions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'permissions': (('errata_xmlrpc_scan', 'Can submit ET scan via XML-RPC'),),
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('description', models.TextField(null=True, blank=True)),
                ('enabled', models.BooleanField(default=True)),
                ('command_arguments', kobo.django.fields.JSONField(default={}, help_text=b"this field has to contain key 'analyzers', which is a comma separated list of analyzers, optionally add key csmock_args, which is a string")),
            ],
        ),
        migrations.CreateModel(
            name='ReleaseMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('release_tag', models.CharField(max_length=32)),
                ('template', models.CharField(max_length=32)),
                ('priority', models.IntegerField()),
            ],
            options={
                'ordering': ['priority'],
            },
        ),
        migrations.CreateModel(
            name='Scan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nvr', models.CharField(help_text=b'Name-Version-Release', max_length=512, verbose_name=b'NVR')),
                ('scan_type', models.PositiveIntegerField(default=0, help_text=b'Scan Type', choices=[(0, b'ERRATA'), (1, b'ERRATA_BASE'), (2, b'USER'), (3, b'REBASE'), (4, b'NEWPKG')])),
                ('state', models.PositiveIntegerField(default=10, help_text=b'Current scan state', choices=[(0, b'QUEUED'), (1, b'SCANNING'), (2, b'NEEDS_INSPECTION'), (3, b'WAIVED'), (4, b'PASSED'), (5, b'FINISHED'), (6, b'FAILED'), (7, b'BASE_SCANNING'), (8, b'CANCELED'), (9, b'DISPUTED'), (10, b'INIT'), (11, b'BUG_CONFIRMED')])),
                ('last_access', models.DateTimeField(null=True, blank=True)),
                ('date_submitted', models.DateTimeField(auto_now_add=True)),
                ('enabled', models.BooleanField(default=True, help_text=b'This scan is counted in statistics.')),
            ],
            options={
                'get_latest_by': 'date_submitted',
            },
        ),
        migrations.CreateModel(
            name='ScanBinding',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'get_latest_by': 'result__date_submitted',
            },
        ),
        migrations.CreateModel(
            name='SystemRelease',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tag', models.CharField(max_length=16, verbose_name=b'Short tag')),
                ('product', models.CharField(max_length=128, verbose_name=b'Product name')),
                ('release', models.IntegerField()),
                ('active', models.BooleanField(default=True, help_text=b'If set to True,statistical data will be harvested for this system release.')),
                ('parent', models.OneToOneField(on_delete=models.CASCADE, null=True, blank=True, to='scan.SystemRelease')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name=b'Brew Tag')),
                ('mock', models.ForeignKey(related_name='mock_profile', verbose_name=b'Mock Config', to='scan.MockConfig', on_delete=models.CASCADE)),
                ('release', models.ForeignKey(related_name='system_release', to='scan.SystemRelease', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='TaskExtension',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('secret_args', kobo.django.fields.JSONField(default={})),
                ('task', models.OneToOneField(on_delete=models.CASCADE, to='hub.Task')),
            ],
        ),
    ]
