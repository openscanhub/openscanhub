# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'ScanningSession.profile'
        db.add_column(u'errata_scanningsession', 'profile',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['scan.Profile'], null=True, blank=True),
                      keep_default=False)

        # Removing M2M table for field analysers on 'Capability'
        db.delete_table('errata_capability_analysers')

        # Adding M2M table for field analyzers on 'Capability'
        db.create_table(u'errata_capability_analyzers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('capability', models.ForeignKey(orm[u'errata.capability'], null=False)),
            ('analyzer', models.ForeignKey(orm[u'scan.analyzer'], null=False))
        ))
        db.create_unique(u'errata_capability_analyzers', ['capability_id', 'analyzer_id'])


    def backwards(self, orm):
        # Deleting field 'ScanningSession.profile'
        db.delete_column(u'errata_scanningsession', 'profile_id')

        # Adding M2M table for field analysers on 'Capability'
        db.create_table(u'errata_capability_analysers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('capability', models.ForeignKey(orm[u'errata.capability'], null=False)),
            ('analyzer', models.ForeignKey(orm[u'scan.analyzer'], null=False))
        ))
        db.create_unique(u'errata_capability_analysers', ['capability_id', 'analyzer_id'])

        # Removing M2M table for field analyzers on 'Capability'
        db.delete_table('errata_capability_analyzers')


    models = {
        u'errata.capability': {
            'Meta': {'object_name': 'Capability'},
            'analyzers': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['scan.Analyzer']", 'symmetrical': 'False'}),
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
            'options': ('kobo.django.fields.JSONField', [], {'default': '{}', 'blank': 'True'}),
            'profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['scan.Profile']", 'null': 'True', 'blank': 'True'})
        },
        u'scan.analyzer': {
            'Meta': {'object_name': 'Analyzer'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
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
        u'scan.profile': {
            'Meta': {'object_name': 'Profile'},
            'command_arguments': ('kobo.django.fields.JSONField', [], {'default': '{}'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
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