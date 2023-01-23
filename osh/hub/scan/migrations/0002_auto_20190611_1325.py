# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('scan', '0001_initial'),
        ('waiving', '0001_initial'),
        ('hub', '0003_auto_20160202_0647'),
    ]

    operations = [
        migrations.AddField(
            model_name='scanbinding',
            name='result',
            field=models.OneToOneField(on_delete=models.CASCADE, null=True, blank=True, to='waiving.Result'),
        ),
        migrations.AddField(
            model_name='scanbinding',
            name='scan',
            field=models.OneToOneField(on_delete=models.CASCADE, verbose_name=b'Scan', to='scan.Scan'),
        ),
        migrations.AddField(
            model_name='scanbinding',
            name='task',
            field=models.OneToOneField(on_delete=models.CASCADE, null=True, to='hub.Task', blank=True, help_text=b'Asociated task on worker', verbose_name=b'Asociated Task'),
        ),
        migrations.AddField(
            model_name='scan',
            name='base',
            field=models.ForeignKey(related_name='base_scan', blank=True, to='scan.Scan', help_text=b'NVR of package to diff against', null=True, verbose_name=b'Base Scan', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='scan',
            name='package',
            field=models.ForeignKey(to='scan.Package', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='scan',
            name='parent',
            field=models.ForeignKey(related_name='parent_scan', verbose_name=b'Parent Scan', blank=True, to='scan.Scan', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='scan',
            name='tag',
            field=models.ForeignKey(blank=True, to='scan.Tag', help_text=b'Tag from brew', null=True, verbose_name=b'Tag', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='scan',
            name='username',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='packagecapability',
            name='package',
            field=models.ForeignKey(to='scan.Package', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='packagecapability',
            name='release',
            field=models.ForeignKey(blank=True, to='scan.SystemRelease', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='packageattribute',
            name='package',
            field=models.ForeignKey(to='scan.Package', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='packageattribute',
            name='release',
            field=models.ForeignKey(to='scan.SystemRelease', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='etmapping',
            name='latest_run',
            field=models.ForeignKey(blank=True, to='scan.ScanBinding', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='clientanalyzer',
            name='analyzer',
            field=models.ForeignKey(blank=True, to='scan.Analyzer', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='analyzerversion',
            name='analyzer',
            field=models.ForeignKey(to='scan.Analyzer', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='analyzerversion',
            name='mocks',
            field=models.ManyToManyField(related_name='analyzers', null=True, to='scan.MockConfig', blank=True),
        ),
    ]
