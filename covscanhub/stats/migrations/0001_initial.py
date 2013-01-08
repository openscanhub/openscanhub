# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'StatType'
        db.create_table('stats_stattype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length='32')),
            ('short_comment', self.gf('django.db.models.fields.CharField')(max_length='128')),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length='512')),
            ('group', self.gf('django.db.models.fields.CharField')(max_length='16')),
            ('order', self.gf('django.db.models.fields.IntegerField')()),
            ('is_release_specific', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('stats', ['StatType'])

        # Adding model 'StatResults'
        db.create_table('stats_statresults', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('stat', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stats.StatType'])),
            ('value', self.gf('django.db.models.fields.IntegerField')()),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('release', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scan.SystemRelease'], null=True, blank=True)),
        ))
        db.send_create_signal('stats', ['StatResults'])


    def backwards(self, orm):
        # Deleting model 'StatType'
        db.delete_table('stats_stattype')

        # Deleting model 'StatResults'
        db.delete_table('stats_statresults')


    models = {
        'scan.systemrelease': {
            'Meta': {'object_name': 'SystemRelease'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['scan.SystemRelease']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'product': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'release': ('django.db.models.fields.IntegerField', [], {}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '16'})
        },
        'stats.statresults': {
            'Meta': {'object_name': 'StatResults'},
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'release': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scan.SystemRelease']", 'null': 'True', 'blank': 'True'}),
            'stat': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stats.StatType']"}),
            'value': ('django.db.models.fields.IntegerField', [], {})
        },
        'stats.stattype': {
            'Meta': {'object_name': 'StatType'},
            'comment': ('django.db.models.fields.CharField', [], {'max_length': "'512'"}),
            'group': ('django.db.models.fields.CharField', [], {'max_length': "'16'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_release_specific': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': "'32'"}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'short_comment': ('django.db.models.fields.CharField', [], {'max_length': "'128'"})
        }
    }

    complete_apps = ['stats']