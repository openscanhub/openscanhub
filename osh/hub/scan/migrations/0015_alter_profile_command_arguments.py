from django.db import migrations


def swap(apps, schema_editor, original, new):
    Profile = apps.get_model('scan', 'profile')
    db_alias = schema_editor.connection.alias

    for p in Profile.objects.using(db_alias):
        if original not in p.command_arguments:
            continue

        p.command_arguments[new] = p.command_arguments[original]
        del p.command_arguments[original]
        p.save()


def forwards_func(apps, schema_editor):
    swap(apps, schema_editor, 'koji_bin', 'koji_profile')


def reverse_func(apps, schema_editor):
    swap(apps, schema_editor, 'koji_profile', 'koji_bin')


class Migration(migrations.Migration):
    dependencies = [
        ('scan', '0014_alter_profile_command_arguments'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func)
    ]
