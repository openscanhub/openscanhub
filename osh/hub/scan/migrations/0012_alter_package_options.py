# Generated by Django 4.0.10 on 2023-05-09 14:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scan', '0011_alter_etmapping_comment'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='package',
            options={'ordering': ['name']},
        ),
    ]