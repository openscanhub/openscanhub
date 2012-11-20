# -*- coding: utf-8 -*-

import types

import django.db.models as models
from django.utils.safestring import mark_safe

import kobo.django.fields

from covscanhub.scan.models import SystemRelease


class StatType(models.Model):
    key = models.CharField("Key", max_length="32", help_text="Short tag that \
describes value of this stat.")
    comment = models.CharField("Value", max_length="512")

    def __unicode__(self):
        return u"%s (%s)" % (self.key, self.comment)


class StatResults(models.Model):
    stat = models.ForeignKey(StatType)
    value = models.IntegerField(
        help_text="Statistical data for specified stat type."
    )
    date = models.DateTimeField(auto_now_add=True, verbose_name="Date created")
    release = models.ForeignKey(SystemRelease, blank=True, null=True)

    class Meta:
        get_latest_by = "date"        

    def __unicode__(self):
        return u"%s = %s" % (self.stat.key, self.value)                