# -*- coding: utf-8 -*-

import django.db.models as models

from covscanhub.scan.models import SystemRelease


class StatType(models.Model):
    key = models.CharField("Key", max_length="32", help_text="Short tag that \
describes value of this stat.")
    short_comment = models.CharField("Description", max_length="128")
    comment = models.CharField("Description", max_length="512")
    group = models.CharField("Description", max_length="16")
    order = models.IntegerField()
    is_release_specific = models.BooleanField()

    def __unicode__(self):
        return u"%s (%s)" % (self.key, self.comment)

    def display_value(self, release=None):
        results = StatResults.objects.filter(stat=self)
        if not results:
            return 0
        if self.is_release_specific and release:
            return results.filter(release=release).latest().value
        else:
            return results.latest().value


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