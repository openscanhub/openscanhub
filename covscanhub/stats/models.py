# -*- coding: utf-8 -*-

import types

import django.db.models as models

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
    value = kobo.django.fields.JSONField(blank=True, null=True, default={},
        help_text="Statistical data for specified stat type.")
    date = models.DateField(auto_now_add=True, verbose_name="Date created")

    class Meta:
        get_latest_by = "date"        


    def display_value(self):
        if isinstance(self.value, types.NoneType):
            return ''
        elif isinstance(self.value, int):
            return self.value
        else:
            response = ""
            for i in enumerate(self.value):
                try:
                    response += "%s = %s, " % (
                        SystemRelease.objects.get(id=i[0]).tag, i[1])
                except IndexError:
                    response += "%s, " % (i[0])
            if len(response) > 50:
                return response[:50] + '...'
            else:
                return response[:len(response) - 2]

    def __unicode__(self):
        return u"%s = %s" % (self.stat.key, self.value)                