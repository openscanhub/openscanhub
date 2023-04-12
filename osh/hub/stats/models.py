import django.db.models as models
from django.urls import reverse

from osh.hub.scan.models import SystemRelease


class StatType(models.Model):
    key = models.CharField("Key", max_length=128, help_text="Short tag that \
describes value of this stat.")
    short_comment = models.CharField("Description", max_length=128)
    comment = models.CharField("Description", max_length=512)
    group = models.CharField("Description", max_length=16)
    order = models.IntegerField()
    is_release_specific = models.BooleanField()

    def __str__(self):
        return "%s (%s)" % (self.key, self.comment)

    def display_value(self, release=None):
        results = StatResults.objects.filter(stat=self)
        if not results:
            return 0
        if self.is_release_specific and release:
            try:
                return results.filter(release=release).latest().value
            except Exception:  # noqa: B902
                return 0
        else:
            return results.latest().value

    def detail_url(self, release=None):
        if self.is_release_specific:
            return reverse(
                'stats/release/detail',
                kwargs={
                    'release_id': release.id,
                    'stat_id': self.id
                }
            )
        else:
            return reverse(
                'stats/detail',
                kwargs={
                    'stat_id': self.id
                }
            )


class StatResults(models.Model):
    stat = models.ForeignKey(StatType, on_delete=models.CASCADE)
    value = models.IntegerField(
        help_text="Statistical data for specified stat type."
    )
    date = models.DateTimeField(auto_now_add=True, verbose_name="Date created")
    release = models.ForeignKey(SystemRelease, blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        get_latest_by = "date"

    def __str__(self):
        return "%s = %s" % (self.stat.key, self.value)
