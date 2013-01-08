# -*- coding: utf-8 -*-

import datetime

from kobo.types import Enum, EnumItem
from kobo.django.fields import JSONField

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
import django.db.models as models

from covscanhub.scan.models import Package, SystemRelease

DEFECT_STATES = Enum(
    # newly introduced defect
    EnumItem("NEW", help_text="Newly introduced defect"),
    # this one was present in base scan -- nothing new
    EnumItem("OLD", help_text="Defect present in base and this scan."),
    # present in base, but no longer in actual version; good job
    EnumItem("FIXED", help_text="Defect fixed by this build."),
    EnumItem("UNKNOWN", help_text="Default value."),
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
    # this is default state and should be changed ASAP
    EnumItem("UNKNOWN", help_text="Unknown state"),
    # this rg was waived in one of the previous runs
    EnumItem("PREVIOUSLY_WAIVED", help_text="Waived in one of previous runs"),
)

#DEFECT_PRIORITY = Enum(
#)

CHECKER_SEVERITIES = Enum(
    EnumItem("NO_EFFECT", help_text="this test does not affect program, could be style issue"),
    EnumItem("FALSE_POSITIVE", help_text="test is not reliable & yields many false positives"),
    EnumItem("UNCLASSIFIED", help_text="the default category"),
    EnumItem("CONFUSION", help_text="the author is confused; could be logic problems nearby"),
    EnumItem("SECURITY", help_text="could be exploited"),
    EnumItem("ROBUSTNESS", help_text="will cause the program to crash or lockup"),
)


class Result(models.Model):
    """
    Result of submited scan is held by this method.
    """
    scanner = models.CharField("Analyser", max_length=32,
                               blank=True, null=True)
    scanner_version = models.CharField("Analyser's Version",
                                       max_length=32, blank=True, null=True)
    lines = models.IntegerField(help_text='Lines of code scanned', blank=True,
                                null=True)
    #time in seconds that scanner spent scanning
    scanning_time = models.IntegerField(verbose_name='Time spent scanning',
                                        blank=True, null=True)
    date_submitted = models.DateTimeField()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.date_submitted = datetime.datetime.now()
        super(Result, self).save(*args, **kwargs)

    class Meta:
        get_latest_by = "date_submitted"

    def get_defects_count(self, defect_type):
        rgs = ResultGroup.objects.filter(result=self,
                                         defect_type=defect_type)
        count = 0
        for rg in rgs:
            count += rg.defects_count
        return count

    def new_defects_count(self):
        return self.get_defects_count(DEFECT_STATES['NEW'])

    def fixed_defects_count(self):
        return self.get_defects_count(DEFECT_STATES['FIXED'])

    def __unicode__(self):
        return "#%d %s %s %s" % (self.id, self.scanner, self.scanner_version,
                                 self.scanbinding.scan)


class Defect(models.Model):
    """
    One Result is composed of several Defects, each Defect is defined by
    some Events where one is key event
    """
    #ARRAY_VS_SINGLETON | BUFFER_SIZE_WARNING
    checker = models.ForeignKey("Checker", verbose_name="Checker",
                                blank=False, null=False)

    order = models.IntegerField(null=True,
                                help_text="Defects in view have fixed order.")

    #priority = models.PositiveIntegerField(default=DEFECT_STATES["UNKNOWN"],
    #                                    choices=DEFECT_STATES.get_mapping(),
    #                                    help_text="Defect state")

    #CWE-xxx
    annotation = models.CharField("Annotation", max_length=32,
                                  blank=True, null=True)
    key_event = models.IntegerField(verbose_name="Key event",
                                    help_text="Event that resulted in defect")
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

    events = JSONField(default=[],
                       help_text="List of defect related events.")

    def __unicode__(self):
        return "#%d Checker: (%s)" % (self.id, self.checker)


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
    defect_type = models.PositiveIntegerField(
        default=DEFECT_STATES["UNKNOWN"],
        choices=DEFECT_STATES.get_mapping(),
        help_text="Type of defects that are associated with this group.")
    defects_count = models.PositiveSmallIntegerField(
        default=0, blank=True, null=True, verbose_name="Number of defects \
associated with this group.")

    def is_previously_waived(self):
        return self.state == RESULT_GROUP_STATES['PREVIOUSLY_WAIVED']

    def get_new_defects(self):
        return Defect.objects.filter(result_group=self.id,
                                     state=DEFECT_STATES['NEW'])

    def is_marked_as_bug(self):
        if self.state == RESULT_GROUP_STATES['WAIVED']:
            try:
                Waiver.objects.get(result_group=self,
                                   state=WAIVER_TYPES['IS_A_BUG'])
                return True
            except ObjectDoesNotExist:
                return False

    def get_state_to_display(self):
        """
        return state for CSS class
        """
        if self.defect_type == DEFECT_STATES['FIXED']:
            if self.defects_count > 0:
                return 'INFO'
            else:
                return 'PASSED'
        elif self.defect_type == DEFECT_STATES["NEW"]:
            if self.defects_count > 0:
                if self.is_marked_as_bug():
                    return 'IS_A_BUG'
                else:
                    return self.get_state_display()
            else:
                return 'PASSED'

    def previous_waivers(self):
        actual_waivers = Waiver.objects.filter(result_group=self)
        if actual_waivers:
            d = actual_waivers.order_by('date')[0].date
        else:
            d = self.result.date_submitted
        w = Waiver.objects.filter(
            result_group__checker_group=self.checker_group,
            date__lt=d,
            result_group__result__scanbinding__scan__package=
                self.result.scanbinding.scan.package
        )
        if w:
            return w.order_by('date')

    def __unicode__(self):
        return "#%d [%s - %s], Result: (%s)" % (
            self.id, self.checker_group.name, self.get_state_display(),
            self.result
        )


class Checker(models.Model):
    """
    Checker is a type of defect.
    """
    name = models.CharField("Checker's name", max_length=32,
                            blank=False, null=False)
    severity = models.PositiveIntegerField(
        default=CHECKER_SEVERITIES["NO_EFFECT"],
        choices=CHECKER_SEVERITIES.get_mapping(),
        help_text="Severity of checker that the defect represents"
    )
    # if you use get_or_create, it will save it
    group = models.ForeignKey(CheckerGroup, verbose_name="Checker group",
                              blank=True, null=True,
                              help_text="Name of group where does this \
checker belong")

    def __unicode__(self):
        return "#%d %s, CheckerGroup: (%s)" % (self.id, self.name, self.group)


class Bugzilla(models.Model):
    number = models.IntegerField()
    package = models.ForeignKey(Package)
    release = models.ForeignKey(SystemRelease)

    def __unicode__(self):
        return u"#%d BZ#%d (%s, %s.%d)" % (
            self.id,
            self.number,
            self.package.name,
            self.release.product,
            self.release.release,
        )


class Waiver(models.Model):
    """
    User acknowledges that he processed this defect
    """
    date = models.DateTimeField()  # date submitted
    message = models.TextField("Message")
    result_group = models.ForeignKey(ResultGroup, blank=False, null=False,
                                     help_text="Group of defects which is \
waived for specific Result")
    user = models.ForeignKey(User)
    state = models.PositiveIntegerField(default=WAIVER_TYPES["IS_A_BUG"],
                                        choices=WAIVER_TYPES.get_mapping(),
                                        help_text="Type of waiver")
    bz = models.ForeignKey(Bugzilla, blank=True, null=True)

    class Meta:
        get_latest_by = "date"

    def __unicode__(self):
        return u"#%d %s - %s, ResultGroup: (%s) BZ: %s" % (
            self.id,
            self.message,
            self.get_state_display(),
            self.result_group,
            self.bz
        )