# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Capability'
        db.create_table(u'errata_capability', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('function', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('options', self.gf('kobo.django.fields.JSONField')(default={}, blank=True)),
        ))
        db.send_create_signal(u'errata', ['Capability'])

        # Adding M2M table for field caps on 'Capability'
        db.create_table(u'errata_capability_caps', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('capability', models.ForeignKey(orm[u'errata.capability'], null=False)),
            ('packagecapability', models.ForeignKey(orm[u'scan.packagecapability'], null=False))
        ))
        db.create_unique(u'errata_capability_caps', ['capability_id', 'packagecapability_id'])

        # Adding M2M table for field analysers on 'Capability'
        db.create_table(u'errata_capability_analysers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('capability', models.ForeignKey(orm[u'errata.capability'], null=False)),
            ('analyzer', models.ForeignKey(orm[u'scan.analyzer'], null=False))
        ))
        db.create_unique(u'errata_capability_analysers', ['capability_id', 'analyzer_id'])

        # Adding model 'ScanningSession'
        db.create_table(u'errata_scanningsession', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('options', self.gf('kobo.django.fields.JSONField')(default={}, blank=True)),
        ))
        db.send_create_signal(u'errata', ['ScanningSession'])

        # Adding M2M table for field caps on 'ScanningSession'
        db.create_table(u'errata_scanningsession_caps', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('scanningsession', models.ForeignKey(orm[u'errata.scanningsession'], null=False)),
            ('capability', models.ForeignKey(orm[u'errata.capability'], null=False))
        ))
        db.create_unique(u'errata_scanningsession_caps', ['scanningsession_id', 'capability_id'])


    def backwards(self, orm):
        # Deleting model 'Capability'
        db.delete_table(u'errata_capability')

        # Removing M2M table for field caps on 'Capability'
        db.delete_table('errata_capability_caps')

        # Removing M2M table for field analysers on 'Capability'
        db.delete_table('errata_capability_analysers')

        # Deleting model 'ScanningSession'
        db.delete_table(u'errata_scanningsession')

        # Removing M2M table for field caps on 'ScanningSession'
        db.delete_table('errata_scanningsession_caps')


    models = {
        u'errata.capability': {
            'Meta': {'object_name': 'Capability'},
            'analysers': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['scan.Analyzer']", 'symmetrical': 'False'}),
            'caps': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['scan.PackageCapability']", 'symmetrical': 'False'}),
            'function': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'options': ('kobo.django.fields.JSONField', [], {'default': '{}', 'blank': 'True'})
        },
        u'errata.scanningsession': {
            'Meta': {'object_name': 'ScanningSession'},
            'caps': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['errata.Capability']", 'symmetrical': 'False'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'options': ('kobo.django.fields.JSONField', [], {'default': '{}', 'blank': 'True'})
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
        u'scan.package': {
            'Meta': {'object_name': 'Package'},
            'blocked': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'eligible': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'scan.packagecapability': {
            'Meta': {'object_name': 'PackageCapability'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_capable': ('django.db.models.fields.BooleanField', [], {}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['scan.Package']"}),
            'release': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['scan.SystemRelease']", 'null': 'True', 'blank': 'True'})
        },
        u'scan.systemrelease': {
            'Meta': {'object_name': 'SystemRelease'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['scan.SystemRelease']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'product': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'release': ('django.db.models.fields.IntegerField', [], {}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '16'})
        }
    }

    complete_apps = ['errata']