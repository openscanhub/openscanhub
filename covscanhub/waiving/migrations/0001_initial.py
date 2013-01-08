# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Result'
        db.create_table('waiving_result', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scanner', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('scanner_version', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('lines', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('scanning_time', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('date_submitted', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('waiving', ['Result'])

        # Adding model 'Defect'
        db.create_table('waiving_defect', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('checker', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['waiving.Checker'])),
            ('order', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('annotation', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('key_event', self.gf('django.db.models.fields.IntegerField')()),
            ('function', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('defect_identifier', self.gf('django.db.models.fields.CharField')(max_length=16, null=True, blank=True)),
            ('state', self.gf('django.db.models.fields.PositiveIntegerField')(default=3)),
            ('result_group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['waiving.ResultGroup'])),
            ('events', self.gf('kobo.django.fields.JSONField')(default=[])),
        ))
        db.send_create_signal('waiving', ['Defect'])

        # Adding model 'CheckerGroup'
        db.create_table('waiving_checkergroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('waiving', ['CheckerGroup'])

        # Adding model 'ResultGroup'
        db.create_table('waiving_resultgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('result', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['waiving.Result'])),
            ('state', self.gf('django.db.models.fields.PositiveIntegerField')(default=4)),
            ('checker_group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['waiving.CheckerGroup'])),
            ('defect_type', self.gf('django.db.models.fields.PositiveIntegerField')(default=3)),
            ('defects_count', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, null=True, blank=True)),
        ))
        db.send_create_signal('waiving', ['ResultGroup'])

        # Adding model 'Checker'
        db.create_table('waiving_checker', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['waiving.CheckerGroup'], null=True, blank=True)),
        ))
        db.send_create_signal('waiving', ['Checker'])

        # Adding model 'Bugzilla'
        db.create_table('waiving_bugzilla', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('number', self.gf('django.db.models.fields.IntegerField')()),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scan.Package'])),
            ('release', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scan.SystemRelease'])),
        ))
        db.send_create_signal('waiving', ['Bugzilla'])

        # Adding model 'Waiver'
        db.create_table('waiving_waiver', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('result_group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['waiving.ResultGroup'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('state', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('bz', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['waiving.Bugzilla'], null=True, blank=True)),
        ))
        db.send_create_signal('waiving', ['Waiver'])


    def backwards(self, orm):
        # Deleting model 'Result'
        db.delete_table('waiving_result')

        # Deleting model 'Defect'
        db.delete_table('waiving_defect')

        # Deleting model 'CheckerGroup'
        db.delete_table('waiving_checkergroup')

        # Deleting model 'ResultGroup'
        db.delete_table('waiving_resultgroup')

        # Deleting model 'Checker'
        db.delete_table('waiving_checker')

        # Deleting model 'Bugzilla'
        db.delete_table('waiving_bugzilla')

        # Deleting model 'Waiver'
        db.delete_table('waiving_waiver')


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
        'scan.package': {
            'Meta': {'object_name': 'Package'},
            'blocked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
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
        'waiving.bugzilla': {
            'Meta': {'object_name': 'Bugzilla'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scan.Package']"}),
            'release': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scan.SystemRelease']"})
        },
        'waiving.checker': {
            'Meta': {'object_name': 'Checker'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['waiving.CheckerGroup']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'waiving.checkergroup': {
            'Meta': {'object_name': 'CheckerGroup'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'waiving.defect': {
            'Meta': {'object_name': 'Defect'},
            'annotation': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'checker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['waiving.Checker']"}),
            'defect_identifier': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'events': ('kobo.django.fields.JSONField', [], {'default': '[]'}),
            'function': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key_event': ('django.db.models.fields.IntegerField', [], {}),
            'order': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'result_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['waiving.ResultGroup']"}),
            'state': ('django.db.models.fields.PositiveIntegerField', [], {'default': '3'})
        },
        'waiving.result': {
            'Meta': {'object_name': 'Result'},
            'date_submitted': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lines': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'scanner': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'scanner_version': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'scanning_time': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'waiving.resultgroup': {
            'Meta': {'object_name': 'ResultGroup'},
            'checker_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['waiving.CheckerGroup']"}),
            'defect_type': ('django.db.models.fields.PositiveIntegerField', [], {'default': '3'}),
            'defects_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['waiving.Result']"}),
            'state': ('django.db.models.fields.PositiveIntegerField', [], {'default': '4'})
        },
        'waiving.waiver': {
            'Meta': {'object_name': 'Waiver'},
            'bz': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['waiving.Bugzilla']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'result_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['waiving.ResultGroup']"}),
            'state': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['waiving']