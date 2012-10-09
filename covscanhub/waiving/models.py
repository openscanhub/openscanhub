# -*- coding: utf-8 -*-

import django.db.models as models
from covscanhub.scan.models import Scan
from kobo.types import Enum


DEFECT_STATES = Enum(
    "NEW",    # newly introduced defect
    "OLD",    # this one was present in base scan -- nothing new
    "FIXED",  # present in base scan, but no longer in actual version; good job
)


class Result(models.Model):
    scanner = models.CharField("Analyser", max_length=32,
                               blank=True, null=True)
    scanner_version = models.CharField("Analyser's Version",
                                       max_length=32, blank=True, null=True)
    scan = models.ForeignKey(Scan, verbose_name="Scan",
                             blank=True, null=True,)
 
    def __unicode__(self):
        return "%s %s" % (self.scanner, self.scanner_version)


class Event(models.Model):
    file_name = models.CharField("Filename", max_length=128,
                                 blank=True, null=True)
    line = models.CharField("Line", max_length=16,
                            blank=True, null=True)
    #check_return | example_assign | unterminated_case | fallthrough
    event = models.CharField("Event", max_length=16,
                             blank=True, null=True)
    message = models.CharField("Message", max_length=256,
                               blank=True, null=True)
    defect = models.ForeignKey('Defect', verbose_name="Defect",
                               blank=True, null=True,)

    def __unicode__(self):
        return "%s:%s, %s" % (self.file_name, self.line, self.event)


class Defect(models.Model):
    #ARRAY_VS_SINGLETON | BUFFER_SIZE_WARNING
    checker = models.ForeignKey("Checker", max_length=64,
                                verbose_name="Checker"
                                blank=False, null=False)
    #CWE-xxx
    annotation = models.CharField("Annotation", max_length=32,
                                  blank=True, null=True)
    key_event = models.OneToOneField(Event, verbose_name="Key event",
                                     blank=True, null=True,
                                     help_text="Event that resulted in defect",
                                     related_name='defect_key_event')
    result = models.ForeignKey(Result, verbose_name="Result",
                               blank=True, null=True,
                               help_text="Result of scan")

    state = models.PositiveIntegerField(default=DEFECT_STATES["NEW"],
                                        choices=DEFECT_STATES.get_mapping(),
                                        help_text="Defect state")
    def __unicode__(self):
        return "%s, %s" % (self.checker, self.annotation)


class CheckerGroup(models.Model):
    name = models.CharField("Checker's name", max_length=32,
                            blank=False, null=False)

    def __unicode__(self):
        return "%s" % (self.name)


class Checker(models.Model):
    name = models.CharField("Checker's name", max_length=32,
                            blank=False, null=False)
    group = models.ForeignKey(CheckerGroup, verbose_name="Checker group",
                              blank=False, null=False,
                              help_text="Name of group where does this \
checker belong")

    def __unicode__(self):
        return "%s: %s" % (self.name, self.group)

class Waiver(models.Model):
    date = models.DateTimeField()
    message = models.TextField("Message")
    result = models.ForeignKey(Result, verbose_name="Result",
                               blank=False, null=False,
                               help_text="Result of scan which is waived")
    group = models.ForeignKey(CheckerGroup, verbose_name="Checker group",
                              blank=False, null=False,
                              help_text="Waiver is associated with this \
checker group")
    user = 

    def __unicode__(self):
        return "%s - %s [%s]" % (self.result, self.group, self.message)