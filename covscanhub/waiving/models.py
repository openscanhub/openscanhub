# -*- coding: utf-8 -*-

import django.db.models as models
from covscanhub.scan.models import Scan


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
    event = models.CharField("Line", max_length=16,
                             blank=True, null=True)
    message = models.CharField("Line", max_length=256,
                               blank=True, null=True)
    defect = models.ForeignKey('Defect', verbose_name="Defect",
                               blank=True, null=True,)

    def __unicode__(self):
        return "%s:%s, %s" % (self.file_name, self.line, self.event)


class Defect(models.Model):
    #ARRAY_VS_SINGLETON | BUFFER_SIZE_WARNING
    checker = models.CharField("Checker", max_length=64,
                               blank=True, null=True)
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

    def __unicode__(self):
        return "%s, %s" % (self.checker, self.annotation)


#class Waive(models.Model):
#    date = models.DateTimeField()
#    message = models.TextField("Message")
#    group = models.ForeignKey(...)