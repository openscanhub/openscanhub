from django.db import migrations


def forwards_func(apps, schema_editor):
    Task = apps.get_model('hub', 'task')

    # manually recompute the subtask count
    for p in Task.objects.all():
        p.subtask_count = Task.objects.filter(parent=p).count()
        p.save()


class Migration(migrations.Migration):
    dependencies = [
        ('hub', '0003_auto_20160202_0647'),
        ('scan', '0015_alter_profile_command_arguments'),
    ]

    operations = [
        migrations.RunPython(forwards_func)
    ]
