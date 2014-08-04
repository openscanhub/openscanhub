# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PackageAttribute'
        db.create_table(u'scan_packageattribute', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scan.Package'])),
            ('release', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scan.SystemRelease'])),
        ))
        db.send_create_signal(u'scan', ['PackageAttribute'])


        # Changing field 'Scan.username'
        db.alter_column(u'scan_scan', 'username_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.LongnameUser']))

        # Changing field 'Package.blocked'
        db.alter_column(u'scan_package', 'blocked', self.gf('django.db.models.fields.NullBooleanField')(null=True))

        # Changing field 'Package.eligible'
        db.alter_column(u'scan_package', 'eligible', self.gf('django.db.models.fields.NullBooleanField')(null=True))

        # Changing field 'AppSettings.value'
        db.alter_column(u'scan_appsettings', 'value', self.gf('django.db.models.fields.TextField')(null=True))

    def backwards(self, orm):
        # Deleting model 'PackageAttribute'
        db.delete_table(u'scan_packageattribute')


        # Changing field 'Scan.username'
        db.alter_column(u'scan_scan', 'username_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'Package.blocked'
        db.alter_column(u'scan_package', 'blocked', self.gf('django.db.models.fields.BooleanField')())

        # Changing field 'Package.eligible'
        db.alter_column(u'scan_package', 'eligible', self.gf('django.db.models.fields.BooleanField')())

        # Changing field 'AppSettings.value'
        db.alter_column(u'scan_appsettings', 'value', self.gf('django.db.models.fields.CharField')(max_length=64, null=True))

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.longnameuser': {
            'Meta': {'object_name': 'LongnameUser', 'db_table': "'auth_user'"},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'hub.arch': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Arch'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '16'}),
            'pretty_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
        },
        u'hub.channel': {
            'Meta': {'object_name': 'Channel'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'hub.task': {
            'Meta': {'ordering': "('-id',)", 'object_name': 'Task'},
            'arch': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['hub.Arch']"}),
            'archive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'args': ('kobo.django.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'awaited': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'channel': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['hub.Channel']"}),
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'dt_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_finished': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dt_started': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'exclusive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.LongnameUser']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['hub.Task']", 'null': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.PositiveIntegerField', [], {'default': '10'}),
            'resubmitted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'resubmitted_by1'", 'null': 'True', 'to': u"orm['auth.LongnameUser']"}),
            'resubmitted_from': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'resubmitted_from1'", 'null': 'True', 'to': u"orm['hub.Task']"}),
            'result': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'state': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'subtask_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'timeout': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'waiting': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'weight': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'worker': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['hub.Worker']", 'null': 'True', 'blank': 'True'})
        },
        u'hub.worker': {
            'Meta': {'object_name': 'Worker'},
            'arches': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['hub.Arch']", 'symmetrical': 'False'}),
            'channels': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['hub.Channel']", 'symmetrical': 'False'}),
            'current_load': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_load': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'blank': 'True'}),
            'max_tasks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'ready': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'task_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'worker_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'blank': 'True'})
        },
        u'scan.analyzer': {
            'Meta': {'ordering': "('id',)", 'object_name': 'Analyzer'},
            'build_append': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'cli_long_command': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'cli_short_command': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'})
        },
        u'scan.appsettings': {
            'Meta': {'object_name': 'AppSettings'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'value': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        u'scan.etmapping': {
            'Meta': {'object_name': 'ETMapping'},
            'advisory_id': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'comment': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            'et_scan_id': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latest_run': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['scan.ScanBinding']", 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        u'scan.mockconfig': {
            'Meta': {'ordering': "('name',)", 'object_name': 'MockConfig'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'})
        },
        u'scan.package': {
            'Meta': {'object_name': 'Package'},
            'blocked': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'eligible': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'scan.packageattribute': {
            'Meta': {'object_name': 'PackageAttribute'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['scan.Package']"}),
            'release': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['scan.SystemRelease']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'})
        },
        u'scan.permissions': {
            'Meta': {'object_name': 'Permissions'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'scan.releasemapping': {
            'Meta': {'ordering': "['priority']", 'object_name': 'ReleaseMapping'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {}),
            'release_tag': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        u'scan.scan': {
            'Meta': {'object_name': 'Scan'},
            'base': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'base_scan'", 'null': 'True', 'to': u"orm['scan.Scan']"}),
            'date_submitted': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_access': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'nvr': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['scan.Package']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'parent_scan'", 'null': 'True', 'to': u"orm['scan.Scan']"}),
            'scan_type': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'state': ('django.db.models.fields.PositiveIntegerField', [], {'default': '10'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['scan.Tag']", 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.LongnameUser']"})
        },
        u'scan.scanbinding': {
            'Meta': {'object_name': 'ScanBinding'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['waiving.Result']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'scan': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['scan.Scan']", 'unique': 'True'}),
            'task': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['hub.Task']", 'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'scan.systemrelease': {
            'Meta': {'object_name': 'SystemRelease'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['scan.SystemRelease']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'product': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'release': ('django.db.models.fields.IntegerField', [], {}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '16'})
        },
        u'scan.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mock': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'mock_profile'", 'to': u"orm['scan.MockConfig']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'release': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'system_release'", 'to': u"orm['scan.SystemRelease']"})
        },
        u'scan.taskextension': {
            'Meta': {'object_name': 'TaskExtension'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'secret_args': ('kobo.django.fields.JSONField', [], {'default': '{}'}),
            'task': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['hub.Task']", 'unique': 'True'})
        },
        u'waiving.result': {
            'Meta': {'object_name': 'Result'},
            'date_submitted': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lines': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'scanner': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'scanner_version': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'scanning_time': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['scan']