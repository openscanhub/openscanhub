# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ETMapping'
        db.create_table('scan_etmapping', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('advisory_id', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('et_scan_id', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('latest_run', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scan.ScanBinding'], null=True, blank=True)),
        ))
        db.send_create_signal('scan', ['ETMapping'])

        # Adding model 'ReleaseMapping'
        db.create_table('scan_releasemapping', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('release_tag', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('template', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('priority', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('scan', ['ReleaseMapping'])

        # Adding model 'AppSettings'
        db.create_table('scan_appsettings', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
        ))
        db.send_create_signal('scan', ['AppSettings'])

        # Adding field 'Package.eligible'
        db.add_column('scan_package', 'eligible',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'ETMapping'
        db.delete_table('scan_etmapping')

        # Deleting model 'ReleaseMapping'
        db.delete_table('scan_releasemapping')

        # Deleting model 'AppSettings'
        db.delete_table('scan_appsettings')

        # Deleting field 'Package.eligible'
        db.delete_column('scan_package', 'eligible')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'hub.arch': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Arch'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '16'}),
            'pretty_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
        },
        'hub.channel': {
            'Meta': {'object_name': 'Channel'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'hub.task': {
            'Meta': {'ordering': "('-id',)", 'object_name': 'Task'},
            'arch': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hub.Arch']"}),
            'archive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'args': ('kobo.django.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'awaited': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'channel': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hub.Channel']"}),
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'dt_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dt_finished': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dt_started': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'exclusive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hub.Task']", 'null': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.PositiveIntegerField', [], {'default': '10'}),
            'resubmitted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'resubmitted_by1'", 'null': 'True', 'to': "orm['auth.User']"}),
            'resubmitted_from': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'resubmitted_from1'", 'null': 'True', 'to': "orm['hub.Task']"}),
            'result': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'state': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'subtask_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'timeout': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'waiting': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'weight': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'worker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hub.Worker']", 'null': 'True', 'blank': 'True'})
        },
        'hub.worker': {
            'Meta': {'object_name': 'Worker'},
            'arches': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['hub.Arch']", 'symmetrical': 'False'}),
            'channels': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['hub.Channel']", 'symmetrical': 'False'}),
            'current_load': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_load': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'blank': 'True'}),
            'max_tasks': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'ready': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'task_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'worker_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'blank': 'True'})
        },
        'scan.appsettings': {
            'Meta': {'object_name': 'AppSettings'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'})
        },
        'scan.etmapping': {
            'Meta': {'object_name': 'ETMapping'},
            'advisory_id': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'et_scan_id': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latest_run': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scan.ScanBinding']", 'null': 'True', 'blank': 'True'})
        },
        'scan.mockconfig': {
            'Meta': {'ordering': "('name',)", 'object_name': 'MockConfig'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'})
        },
        'scan.package': {
            'Meta': {'object_name': 'Package'},
            'blocked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'eligible': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'scan.permissions': {
            'Meta': {'object_name': 'Permissions'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'scan.releasemapping': {
            'Meta': {'ordering': "['priority']", 'object_name': 'ReleaseMapping'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {}),
            'release_tag': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'scan.scan': {
            'Meta': {'object_name': 'Scan'},
            'base': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'base_scan'", 'null': 'True', 'to': "orm['scan.Scan']"}),
            'date_submitted': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_access': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'nvr': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scan.Package']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'parent_scan'", 'null': 'True', 'to': "orm['scan.Scan']"}),
            'scan_type': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'state': ('django.db.models.fields.PositiveIntegerField', [], {'default': '10'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scan.Tag']", 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'scan.scanbinding': {
            'Meta': {'object_name': 'ScanBinding'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['waiving.Result']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'scan': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['scan.Scan']", 'unique': 'True'}),
            'task': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hub.Task']", 'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        'scan.systemrelease': {
            'Meta': {'object_name': 'SystemRelease'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['scan.SystemRelease']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'product': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'release': ('django.db.models.fields.IntegerField', [], {}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '16'})
        },
        'scan.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mock': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'mock_profile'", 'to': "orm['scan.MockConfig']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'release': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'system_release'", 'to': "orm['scan.SystemRelease']"})
        },
        'waiving.result': {
            'Meta': {'object_name': 'Result'},
            'date_submitted': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lines': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'scanner': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'scanner_version': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'scanning_time': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['scan']
