from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('errata', '0001_initial'),
        ('scan', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='scanningsession',
            name='profile',
            field=models.ForeignKey(blank=True, on_delete=models.CASCADE,
                                    to='scan.Profile', null=True),
        ),
        migrations.AddField(
            model_name='capability',
            name='analyzers',
            field=models.ManyToManyField(to='scan.Analyzer'),
        ),
        migrations.AddField(
            model_name='capability',
            name='caps',
            field=models.ManyToManyField(to='scan.PackageCapability'),
        ),
    ]
