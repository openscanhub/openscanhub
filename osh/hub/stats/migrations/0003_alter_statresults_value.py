# Generated by Django 3.2.18 on 2023-04-12 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0002_auto_20211223_1124'),
    ]

    operations = [
        migrations.AlterField(
            model_name='statresults',
            name='value',
            field=models.BigIntegerField(help_text='Statistical data for specified stat type.'),
        ),
    ]
