# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scan', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StatResults',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.IntegerField(help_text=b'Statistical data for specified stat type.')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name=b'Date created')),
                ('release', models.ForeignKey(blank=True, to='scan.SystemRelease', null=True, on_delete=models.CASCADE)),
            ],
            options={
                'get_latest_by': 'date',
            },
        ),
        migrations.CreateModel(
            name='StatType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(help_text=b'Short tag that describes value of this stat.', max_length=128, verbose_name=b'Key')),
                ('short_comment', models.CharField(max_length=128, verbose_name=b'Description')),
                ('comment', models.CharField(max_length=512, verbose_name=b'Description')),
                ('group', models.CharField(max_length=16, verbose_name=b'Description')),
                ('order', models.IntegerField()),
                ('is_release_specific', models.BooleanField()),
            ],
        ),
        migrations.AddField(
            model_name='statresults',
            name='stat',
            field=models.ForeignKey(to='stats.StatType', on_delete=models.CASCADE),
        ),
    ]
