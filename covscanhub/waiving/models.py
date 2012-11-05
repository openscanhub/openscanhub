# -*- coding: utf-8 -*-

import django.db.models as models
from covscanhub.scan.models import Scan
from kobo.types import Enum, EnumItem
from django.contrib.auth.models import User


DEFECT_STATES = Enum(
    "NEW",      # newly introduced defect
    "OLD",      # this one was present in base scan -- nothing new
    "FIXED",    # present in base, but no longer in actual version; good job
    "UNKNOWN",  # default value
)

WAIVER_TYPES = Enum(
    # defect is not a bug
    EnumItem("NOT_A_BUG", help_text="Not a bug"),
    # defect is a bug and I'm going to fix it
    EnumItem("IS_A_BUG", help_text="Is a bug"),
    # defect is a bug and I'm going to fix it in next version
    EnumItem("FIX_LATER", help_text="Fix later"),
)


class Result(models.Model):
    """
    Result of submited scan is held by this method.
    """
    scanner = models.CharField("Analyser", max_length=32,
                               blank=True, null=True)
    scanner_version = models.CharField("Analyser's Version",
                                       max_length=32, blank=True, null=True)
    scan = models.ForeignKey(Scan, verbose_name="Scan",
                             blank=True, null=True,)

    def __unicode__(self):
        return "%s (%s %s)" % (self.scan.nvr, self.scanner,
                               self.scanner_version)


class Event(models.Model):
    """
    Each Event is associated with some Defect. Event represents error in
    specified file on exact line with appropriate message.
    """
    file_name = models.CharField("Filename", max_length=128,
                                 blank=True, null=True)
    line = models.CharField("Line", max_length=8,
                            blank=True, null=True)
    column = models.CharField("Column", max_length=8,
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
    """
    One Result is composed of several Defects, each Defect is defined by
    some Events where one is key event
    """
    #ARRAY_VS_SINGLETON | BUFFER_SIZE_WARNING
    checker = models.ForeignKey("Checker", max_length=64,
                                verbose_name="Checker",
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
    function = models.CharField("Function", max_length=128,
                                help_text="Name of function that contains \
current defect",
                                blank=True, null=True)
    defect_identifier = models.CharField("Defect Identifier", max_length=16,
                                         blank=True, null=True)

    state = models.PositiveIntegerField(default=DEFECT_STATES["UNKNOWN"],
                                        choices=DEFECT_STATES.get_mapping(),
                                        help_text="Defect state")
    def __unicode__(self):
        return "%s, %s" % (self.checker, self.annotation)


class CheckerGroup(models.Model):
    """
    We don't want users to waive each defect so instead we compose checkers
    into specified groups and users waive these groups.
    """
    name = models.CharField("Checker's name", max_length=32,
                            blank=False, null=False)

    def __unicode__(self):
        return "%s" % (self.name)


class Checker(models.Model):
    """
    Checker is a type of defect.
    """
    name = models.CharField("Checker's name", max_length=32,
                            blank=False, null=False)
    group = models.ForeignKey(CheckerGroup, verbose_name="Checker group",
                              blank=False, null=False,
                              help_text="Name of group where does this \
checker belong")

    def __unicode__(self):
        return "%s: %s" % (self.name, self.group)


class Waiver(models.Model):
    """
    User acknowledges that he processed this defect
    """
    date = models.DateTimeField()
    message = models.TextField("Message")
    result = models.ForeignKey(Result, verbose_name="Result",
                               blank=False, null=False,
                               help_text="Result of scan which is waived")
    group = models.ForeignKey(CheckerGroup, verbose_name="Checker group",
                              blank=False, null=False,
                              help_text="Waiver is associated with this \
checker group")
    user = models.ForeignKey(User)
    state = models.PositiveIntegerField(default=WAIVER_TYPES["IS_A_BUG"],
                                        choices=WAIVER_TYPES.get_mapping(),
                                        help_text="Type of waiver")

    def __unicode__(self):
        return "%s - %s [%s, %s]" % (self.message, self.get_state_display(),
                                     self.result, self.group)