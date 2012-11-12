# -*- coding: utf-8 -*-

from covscanhub.scan.models import Scan

from kobo.types import Enum, EnumItem

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
import django.db.models as models


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

RESULT_GROUP_STATES = Enum(
    # there are some new defects found which need to be reviewed
    EnumItem("NEEDS_INSPECTION", help_text="Needs inspection"),
    # newly added bugs are rewieved and waived
    EnumItem("WAIVED", help_text="Is a bug"),
    # there are no new defects, only fixed one, developer might
    # want to see those
    EnumItem("INFO", help_text="Fix later"),
    # there are no defects associated with this checker group
    EnumItem("PASSED", help_text="Fix later"),
    # this is default state and should be changes ASAP
    EnumItem("UNKNOWN", help_text="Unknown state"),
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
    lines = models.IntegerField(help_text='Lines of code scanned', blank=True,
                                null=True)
    def __unicode__(self):
        return "#%d %s (%s %s)" % (self.id, self.scan.nvr, self.scanner,
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

    def line_and_column(self):
        return '%s:%s' % (self.line, self.column) if self.column else self.line

    def __unicode__(self):
        return "#%d %s:%s, %s" % (self.id, self.file_name,
                                  self.line, self.event)


class Defect(models.Model):
    """
    One Result is composed of several Defects, each Defect is defined by
    some Events where one is key event
    """
    #ARRAY_VS_SINGLETON | BUFFER_SIZE_WARNING
    checker = models.ForeignKey("Checker", verbose_name="Checker",
                                blank=False, null=False)
    #CWE-xxx
    annotation = models.CharField("Annotation", max_length=32,
                                  blank=True, null=True)
    key_event = models.OneToOneField(Event, verbose_name="Key event",
                                     blank=True, null=True,
                                     help_text="Event that resulted in defect",
                                     related_name='defect_key_event')
    function = models.CharField("Function", max_length=128,
                                help_text="Name of function that contains \
current defect",
                                blank=True, null=True)
    defect_identifier = models.CharField("Defect Identifier", max_length=16,
                                         blank=True, null=True)
    state = models.PositiveIntegerField(default=DEFECT_STATES["UNKNOWN"],
                                        choices=DEFECT_STATES.get_mapping(),
                                        help_text="Defect state")
    result_group = models.ForeignKey('ResultGroup', blank=False, null=False)

    def __unicode__(self):
        return "#%d %s, %s" % (self.id, self.checker, self.annotation)


class CheckerGroup(models.Model):
    """
    We don't want users to waive each defect so instead we compose checkers
    into specified groups and users waive these groups.
    """
    name = models.CharField("Checker's name", max_length=32,
                            blank=False, null=False)
    enabled = models.BooleanField(default=True, help_text="User may waive \
only ResultGroups which belong to enabled CheckerGroups")

    def __unicode__(self):
        return "#%d %s" % (self.id, self.name)


class ResultGroup(models.Model):
    """
    Each set of defects from existed Result that belongs to some CheckGroup is
    represented by this model
    """
    result = models.ForeignKey(Result, verbose_name="Result",
                               help_text="Result of scan")
    state = models.PositiveIntegerField(
        default=RESULT_GROUP_STATES["UNKNOWN"],
        choices=RESULT_GROUP_STATES.get_mapping(),
        help_text="Type of waiver")
    checker_group = models.ForeignKey(CheckerGroup,
                                      verbose_name="Group of checkers")

    def display_in_waiver(self, state):
        """
        return HTML formatted representation of result group displayed in
         waiver, if there are some defects related to this group, create link
         and display number of defects
        @param state: 'NEW' | 'FIXED'
        """
        defects = Defect.objects.filter(result_group=self.id,
                                        state=DEFECT_STATES[state])
        group_state = self.get_state_display()
        checker_group = self.checker_group.name
        response = '<td class="%s">' % group_state
        if defects.count() > 0:
            url = reverse('waiving/waiver', args=(self.result.id, self.id))
            response += '<a href="%s">' % url
        response += checker_group
        if defects.count() > 0:
            response += ' (<span class="%s">%s</span>)</a>' % (state,
                                                               defects.count())
        response += '</td>'
        return response

    def __unicode__(self):
        return "#%d [%s - %s], %s" % (self.id, self.checker_group.name,
                                      self.get_state_display(), self.result)


class Checker(models.Model):
    """
    Checker is a type of defect.
    """
    name = models.CharField("Checker's name", max_length=32,
                            blank=False, null=False)
    # if you use get_or_create, it will save it
    group = models.ForeignKey(CheckerGroup, verbose_name="Checker group",
                              blank=True, null=True,
                              help_text="Name of group where does this \
checker belong")

    def __unicode__(self):
        return "#%d %s: %s" % (self.id, self.name, self.group)


class Waiver(models.Model):
    """
    User acknowledges that he processed this defect
    """
    date = models.DateTimeField()
    message = models.TextField("Message")
    result_group = models.ForeignKey(ResultGroup, blank=False, null=False,
                                     help_text="Group of defects which is \
waived for specific Result")
    user = models.ForeignKey(User)
    state = models.PositiveIntegerField(default=WAIVER_TYPES["IS_A_BUG"],
                                        choices=WAIVER_TYPES.get_mapping(),
                                        help_text="Type of waiver")

    def __unicode__(self):
        return "#%d %s - %s [%s]" % (self.id, self.message,
                                     self.get_state_display(),
                                     self.result_group)