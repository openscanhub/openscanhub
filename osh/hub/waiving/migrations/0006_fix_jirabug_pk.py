# Generated by Django 3.2.19 on 2023-05-17 02:04

import django.db.models.deletion
from django.db import migrations, models


def convert_jira_bug(apps, schema_editor):
    JiraBug = apps.get_model('waiving', 'JiraBug')
    JiraBug2 = apps.get_model('waiving', 'JiraBug2')
    for jb in JiraBug.objects.all():
        jb2 = JiraBug2(key=jb.key, package=jb.package, release=jb.release)
        jb2.save()
        for w in jb.waiver_set.all():
            w.jira_bug2 = jb2
            w.save()


class Migration(migrations.Migration):

    dependencies = [
        ('scan', '0012_alter_package_options'),
        ('waiving', '0005_alter_defect_events'),
    ]

    operations = [
        # first, we create a new model with the correct PK
        migrations.CreateModel(
            name='JiraBug2',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=64)),
                ('package', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scan.package')),
                ('release', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scan.systemrelease')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='waiver',
            name='jira_bug2',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='waiving.jirabug2'),
        ),
        # then, we copy the data from the old model to the new one
        migrations.RunPython(convert_jira_bug),

        # now we can delete the old model
        migrations.RemoveField(
            model_name='waiver',
            name='jira_bug',
        ),
        migrations.DeleteModel(
            name='JiraBug',
        ),

        # and rename the new model to the old name
        migrations.RenameModel(
            old_name='JiraBug2',
            new_name='JiraBug',
        ),
        migrations.RenameField(
            model_name='waiver',
            old_name='jira_bug2',
            new_name='jira_bug',
        ),
    ]
