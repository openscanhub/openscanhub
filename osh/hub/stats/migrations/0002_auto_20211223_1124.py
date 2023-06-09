# Generated by Django 2.2.24 on 2021-12-23 11:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='statresults',
            name='date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Date created'),
        ),
        migrations.AlterField(
            model_name='statresults',
            name='value',
            field=models.IntegerField(help_text='Statistical data for specified stat type.'),
        ),
        migrations.AlterField(
            model_name='stattype',
            name='comment',
            field=models.CharField(max_length=512, verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='stattype',
            name='group',
            field=models.CharField(max_length=16, verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='stattype',
            name='key',
            field=models.CharField(help_text='Short tag that describes value of this stat.', max_length=128, verbose_name='Key'),
        ),
        migrations.AlterField(
            model_name='stattype',
            name='short_comment',
            field=models.CharField(max_length=128, verbose_name='Description'),
        ),
    ]
