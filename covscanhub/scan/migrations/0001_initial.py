# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Permissions'
        db.create_table(u'scan_permissions', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'scan', ['Permissions'])

        # Adding model 'MockConfig'
        db.create_table(u'scan_mockconfig', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=256)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'scan', ['MockConfig'])

        # Adding model 'SystemRelease'
        db.create_table(u'scan_systemrelease', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tag', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('product', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('release', self.gf('django.db.models.fields.IntegerField')()),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('parent', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['scan.SystemRelease'], unique=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'scan', ['SystemRelease'])

        # Adding model 'Tag'
        db.create_table(u'scan_tag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('mock', self.gf('django.db.models.fields.related.ForeignKey')(related_name='mock_profile', to=orm['scan.MockConfig'])),
            ('release', self.gf('django.db.models.fields.related.ForeignKey')(related_name='system_release', to=orm['scan.SystemRelease'])),
        ))
        db.send_create_signal(u'scan', ['Tag'])

        # Adding model 'Package'
        db.create_table(u'scan_package', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('blocked', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('eligible', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'scan', ['Package'])

        # Adding model 'PackageAttribute'
        db.create_table(u'scan_packageattribute', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scan.Package'])),
            ('release', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scan.SystemRelease'])),
        ))
        db.send_create_signal(u'scan', ['PackageAttribute'])

        # Adding model 'Scan'
        db.create_table(u'scan_scan', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nvr', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('scan_type', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('state', self.gf('django.db.models.fields.PositiveIntegerField')(default=10)),
            ('base', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='base_scan', null=True, to=orm['scan.Scan'])),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scan.Tag'], null=True, blank=True)),
            ('username', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.LongnameUser'])),
            ('last_access', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('date_submitted', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scan.Package'])),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='parent_scan', null=True, to=orm['scan.Scan'])),
        ))
        db.send_create_signal(u'scan', ['Scan'])

        # Adding model 'ScanBinding'
        db.create_table(u'scan_scanbinding', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['hub.Task'], unique=True, null=True, blank=True)),
            ('scan', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['scan.Scan'], unique=True)),
            ('result', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['waiving.Result'], unique=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'scan', ['ScanBinding'])

        # Adding model 'ReleaseMapping'
        db.create_table(u'scan_releasemapping', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('release_tag', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('template', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('priority', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'scan', ['ReleaseMapping'])

        # Adding model 'ETMapping'
        db.create_table(u'scan_etmapping', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('advisory_id', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('et_scan_id', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('latest_run', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scan.ScanBinding'], null=True, blank=True)),
            ('comment', self.gf('django.db.models.fields.CharField')(default='', max_length=256, blank=True)),
            ('state', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal(u'scan', ['ETMapping'])

        # Adding model 'AppSettings'
        db.create_table(u'scan_appsettings', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('value', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'scan', ['AppSettings'])

        # Adding model 'TaskExtension'
        db.create_table(u'scan_taskextension', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['hub.Task'], unique=True)),
            ('secret_args', self.gf('kobo.django.fields.JSONField')(default={})),
        ))
        db.send_create_signal(u'scan', ['TaskExtension'])

        # Adding model 'Analyzer'
        db.create_table(u'scan_analyzer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('cli_short_command', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('cli_long_command', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('build_append', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('default', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'scan', ['Analyzer'])


    def backwards(self, orm):
        # Deleting model 'Permissions'
        db.delete_table(u'scan_permissions')

        # Deleting model 'MockConfig'
        db.delete_table(u'scan_mockconfig')

        # Deleting model 'SystemRelease'
        db.delete_table(u'scan_systemrelease')

        # Deleting model 'Tag'
        db.delete_table(u'scan_tag')

        # Deleting model 'Package'
        db.delete_table(u'scan_package')

        # Deleting model 'PackageAttribute'
        db.delete_table(u'scan_packageattribute')

        # Deleting model 'Scan'
        db.delete_table(u'scan_scan')

        # Deleting model 'ScanBinding'
        db.delete_table(u'scan_scanbinding')

        # Deleting model 'ReleaseMapping'
        db.delete_table(u'scan_releasemapping')

        # Deleting model 'ETMapping'
        db.delete_table(u'scan_etmapping')

        # Deleting model 'AppSettings'
        db.delete_table(u'scan_appsettings')

        # Deleting model 'TaskExtension'
        db.delete_table(u'scan_taskextension')

        # Deleting model 'Analyzer'
        db.delete_table(u'scan_analyzer')


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
            'blocked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'eligible': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
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