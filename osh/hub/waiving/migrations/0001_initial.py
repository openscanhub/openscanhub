# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import migrations, models
from django.conf import settings
import kobo.django.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('scan', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bugzilla',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.IntegerField()),
                ('package', models.ForeignKey(to='scan.Package', on_delete=models.CASCADE)),
                ('release', models.ForeignKey(to='scan.SystemRelease', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Checker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name=b"Checker's name")),
                ('severity', models.PositiveIntegerField(default=0, help_text=b'Severity of checker that the defect represents', choices=[(0, b'NO_EFFECT'), (1, b'FALSE_POSITIVE'), (2, b'UNCLASSIFIED'), (3, b'CONFUSION'), (4, b'SECURITY'), (5, b'ROBUSTNESS')])),
            ],
        ),
        migrations.CreateModel(
            name='CheckerGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name=b"Checker's name")),
                ('enabled', models.BooleanField(default=True, help_text=b'User may waive only ResultGroups which belong to enabled CheckerGroups')),
            ],
        ),
        migrations.CreateModel(
            name='Defect',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(help_text=b'Defects in view have fixed order.', null=True)),
                ('annotation', models.CharField(max_length=32, null=True, verbose_name=b'Annotation', blank=True)),
                ('cwe', models.IntegerField(null=True, verbose_name=b'CWE', blank=True)),
                ('key_event', models.IntegerField(help_text=b'Event that resulted in defect', verbose_name=b'Key event')),
                ('function', models.CharField(help_text=b'Name of function that contains current defect', max_length=128, null=True, verbose_name=b'Function', blank=True)),
                ('defect_identifier', models.CharField(max_length=16, null=True, verbose_name=b'Defect Identifier', blank=True)),
                ('state', models.PositiveIntegerField(default=3, help_text=b'Defect state', choices=[(0, b'NEW'), (1, b'OLD'), (2, b'FIXED'), (3, b'UNKNOWN'), (4, b'PREVIOUSLY_WAIVED')])),
                ('events', kobo.django.fields.JSONField(default=[], help_text=b'List of defect related events.')),
                ('checker', models.ForeignKey(verbose_name=b'Checker', to='waiving.Checker', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('scanner', models.CharField(help_text=b'DEPRECATED, not used anymore', max_length=32, null=True, verbose_name=b'Analyser', blank=True)),
                ('scanner_version', models.CharField(help_text=b'DEPRECATED, not used anymore', max_length=32, null=True, verbose_name=b"Analyser's Version", blank=True)),
                ('lines', models.IntegerField(help_text=b'Lines of code scanned', null=True, blank=True)),
                ('scanning_time', models.IntegerField(null=True, verbose_name=b'Time spent scanning', blank=True)),
                ('date_submitted', models.DateTimeField()),
                ('analyzers', models.ManyToManyField(to='scan.AnalyzerVersion')),
            ],
            options={
                'get_latest_by': 'date_submitted',
            },
        ),
        migrations.CreateModel(
            name='ResultGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('state', models.PositiveIntegerField(default=4, help_text=b'Type of waiver', choices=[(0, b'NEEDS_INSPECTION'), (1, b'WAIVED'), (2, b'INFO'), (3, b'PASSED'), (4, b'UNKNOWN'), (5, b'PREVIOUSLY_WAIVED'), (6, b'CONTAINS_BUG')])),
                ('defect_type', models.PositiveIntegerField(default=3, help_text=b'Type of defects that are associated with this group.', choices=[(0, b'NEW'), (1, b'OLD'), (2, b'FIXED'), (3, b'UNKNOWN'), (4, b'PREVIOUSLY_WAIVED')])),
                ('defects_count', models.PositiveSmallIntegerField(default=0, null=True, verbose_name=b'Number of defects associated with this group.', blank=True)),
                ('checker_group', models.ForeignKey(verbose_name=b'Group of checkers', to='waiving.CheckerGroup', on_delete=models.CASCADE)),
                ('result', models.ForeignKey(verbose_name=b'Result', to='waiving.Result', help_text=b'Result of scan', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Waiver',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('message', models.TextField(verbose_name=b'Message')),
                ('state', models.PositiveIntegerField(default=1, help_text=b'Type of waiver', choices=[(0, b'NOT_A_BUG'), (1, b'IS_A_BUG'), (2, b'FIX_LATER'), (3, b'COMMENT')])),
                ('is_deleted', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=False)),
                ('bz', models.ForeignKey(blank=True, to='waiving.Bugzilla', null=True, on_delete=models.CASCADE)),
                ('result_group', models.ForeignKey(help_text=b'Group of defects which is waived for specific Result', to='waiving.ResultGroup', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('-date',),
                'get_latest_by': 'date',
            },
        ),
        migrations.CreateModel(
            name='WaivingLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('state', models.PositiveIntegerField(help_text=b'Waiving action', choices=[(0, b'NEW'), (1, b'DELETE'), (2, b'REWAIVE')])),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('waiver', models.ForeignKey(to='waiving.Waiver', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['date'],
            },
        ),
        migrations.AddField(
            model_name='defect',
            name='result_group',
            field=models.ForeignKey(to='waiving.ResultGroup', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='checker',
            name='group',
            field=models.ForeignKey(blank=True, to='waiving.CheckerGroup', help_text=b'Name of group where does this checker belong', null=True, verbose_name=b'Checker group', on_delete=models.CASCADE),
        ),
    ]
