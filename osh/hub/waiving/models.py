# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import datetime
import logging

from django.conf import settings
from django.db import models, transaction
from kobo.types import Enum, EnumItem

from osh.hub.scan.models import (SCAN_TYPES, AnalyzerVersion, Package,
                                 SystemRelease)

logger = logging.getLogger(__name__)


DEFECT_STATES = Enum(
    # newly introduced defect
    EnumItem("NEW", help_text="Newly introduced defect"),
    # this one was present in base scan -- nothing new
    EnumItem("OLD", help_text="Defect present in base and this scan."),
    # present in base, but no longer in actual version; good job
    EnumItem("FIXED", help_text="Defect fixed by this build."),
    EnumItem("UNKNOWN", help_text="Default value."),
    EnumItem("PREVIOUSLY_WAIVED", help_text="Defect was waived in a past."),
)

WAIVER_TYPES = Enum(
    # defect is not a bug
    EnumItem("NOT_A_BUG", help_text="Not a bug"),
    # defect is a bug and I'm going to fix it
    EnumItem("IS_A_BUG", help_text="Is a bug"),
    # defect is a bug and I'm going to fix it in next version
    EnumItem("FIX_LATER", help_text="Fix later"),
    # just a comment, no semantics behind
    EnumItem("COMMENT", help_text="Comment"),
)

WAIVERS_ONLY = (
    WAIVER_TYPES['NOT_A_BUG'],
    WAIVER_TYPES['IS_A_BUG'],
    WAIVER_TYPES['FIX_LATER'],
)

WAIVER_TYPES_HELP_TEXTS = {
    "NOT_A_BUG": "all defects in this group are false positives ",
    "IS_A_BUG": "at least one defect in this group is a bug and should be fixed. Please, fix the defects and do a respin.",
    "FIX_LATER": "there are defects in this group and will be fixed in future (in next release probably). Reporting them (or sending patches to) upstream is a good idea.",
    "COMMENT": "inform maintainer about something related to defects in this group",
}

WAIVER_LOG_ACTIONS = Enum(
    EnumItem("NEW", help_text="New entry"),
    EnumItem("DELETE", help_text="Delete existing waiver"),
    EnumItem("REWAIVE", help_text="Change current waiver"),
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
    EnumItem("CONTAINS_BUG", help_text="Group contains bug, which should be fixed."),
)

RESULT_GROUP_PROCESSED = (
    RESULT_GROUP_STATES['WAIVED'],
    RESULT_GROUP_STATES['CONTAINS_BUG'],
)

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
    lines = models.IntegerField(help_text='Lines of code scanned', blank=True,
                                null=True)
    # time in seconds that scanner spent scanning
    scanning_time = models.IntegerField(verbose_name='Time spent scanning',
                                        blank=True, null=True)
    date_submitted = models.DateTimeField()

    analyzers = models.ManyToManyField(AnalyzerVersion)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.date_submitted = datetime.datetime.now()
        super().save(*args, **kwargs)

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

    @property
    def display_title(self):
        new = self.resultgroup_set.filter(defect_type=DEFECT_STATES['NEW'])
        rpr = new.values('state').annotate(count=models.Count("state"))
        result = []
        for state in rpr:
            result.append("%s = %d" % (
                RESULT_GROUP_STATES.get_value(state['state']),
                state['count'],
            ))
        return "\n".join(result)

    @property
    def bugs_count(self):
        contains_bug = self.resultgroup_set.filter(state=RESULT_GROUP_STATES['CONTAINS_BUG'])
        contains_bug_count = contains_bug.count()
        if contains_bug_count != 0:
            return contains_bug_count
        else:
            return self.resultgroup_set.filter(
                waiver__is_active=True,
                waiver__state__in=[WAIVER_TYPES['IS_A_BUG'],
                                   WAIVER_TYPES['FIX_LATER']]
            ).count()

    def has_bugs(self):
        return self.resultgroup_set.filter(
            state=RESULT_GROUP_STATES['CONTAINS_BUG']
        ).exists()

    def set_analyzers(self, analyzers_list):
        """
        set analyzers, input is list of dicts:
            [{'name': ..., 'version': ...}, ...]
        """
        # apparently, if this is NOT wrapped in transaction, none of the relations is saved
        # this is happening in django 1.6, sqlite
        with transaction.atomic():
            for a in analyzers_list:
                try:
                    av = AnalyzerVersion.objects.get_or_create_(a['name'], a['version'])
                except KeyError:
                    logger.error("%s misses either name or version" % a)
                    continue
                self.analyzers.add(av)
        logger.debug("used analyzers = %s", self.analyzers.all())

    def __str__(self):
        return "#%d" % self.id


class DefectMixin:
    def by_release(self, release):
        return self.filter(
            result_group__result__scanbinding__scan__tag__release=release)

    def enabled(self):
        return self.filter(
            result_group__result__scanbinding__scan__enabled=True)

    def fixed(self):
        return self.filter(state=DEFECT_STATES['FIXED'])

    def new(self):
        return self.filter(state=DEFECT_STATES['NEW'])

    def updates(self):
        """ return all defects for regular updates """
        return self.filter(
            result_group__result__scanbinding__scan__scan_type=SCAN_TYPES['ERRATA'])

    def rebases(self):
        """ return all defects for rebases """
        return self.filter(
            result_group__result__scanbinding__scan__scan_type=SCAN_TYPES['REBASE'])


class DefectQuerySet(models.query.QuerySet, DefectMixin):
    pass


class DefectManager(models.Manager, DefectMixin):
    def get_queryset(self):
        """ return all active waivers """
        return DefectQuerySet(self.model, using=self._db)


class Defect(models.Model):
    """
    One Result is composed of several Defects, each Defect is defined by
    some Events where one is key event
    """
    # ARRAY_VS_SINGLETON | BUFFER_SIZE_WARNING
    checker = models.ForeignKey("Checker", verbose_name="Checker",
                                blank=False, null=False, on_delete=models.CASCADE)

    order = models.IntegerField(null=True,
                                help_text="Defects in view have fixed order.")

    # practically anything
    annotation = models.CharField("Annotation", max_length=32,
                                  blank=True, null=True)

    cwe = models.IntegerField("CWE", blank=True, null=True)

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
    result_group = models.ForeignKey('ResultGroup', blank=False, null=False, on_delete=models.CASCADE)

    events = models.JSONField(default=list,
                              help_text="List of defect related events.")

    objects = DefectManager()

    def __str__(self):
        return "#%d Checker: (%s)" % (self.id, self.checker)


class CheckerGroup(models.Model):
    """
    We don't want users to waive each defect so instead we compose checkers
    into specified groups and users waive these groups.
    """
    name = models.CharField("Checker's name", max_length=64,
                            blank=False, null=False)
    enabled = models.BooleanField(default=True, help_text="User may waive \
only ResultGroups which belong to enabled CheckerGroups")

    def __str__(self):
        return "#%d %s" % (self.id, self.name)


class ResultGroupMixin:
    def needs_insp(self):
        return self.filter(state=RESULT_GROUP_STATES['NEEDS_INSPECTION'])

    def active(self):
        return self.filter(result__scanbinding__scan__enabled=True)

    def missing_waiver(self):
        return self.active().needs_insp()

    def by_release(self, release):
        return self.filter(result__scanbinding__scan__tag__release=release)

    def updates(self):
        """ return all rgs for regular updates """
        return self.filter(
            result__scanbinding__scan__scan_type=SCAN_TYPES['ERRATA'])

    def newpkgs(self):
        """ return all rgs for newpkgs """
        return self.filter(
            result__scanbinding__scan__scan_type=SCAN_TYPES['NEWPKG'])

    def rebases(self):
        """ return all rgs for rebases """
        return self.filter(
            result__scanbinding__scan__scan_type=SCAN_TYPES['REBASE'])


class ResultGroupQuerySet(models.query.QuerySet, ResultGroupMixin):
    pass


class ResultGroupManager(models.Manager, ResultGroupMixin):
    def get_queryset(self):
        """ return all active waivers """
        return ResultGroupQuerySet(self.model, using=self._db)


class ResultGroup(models.Model):
    """
    Each set of defects from existed Result that belongs to some CheckGroup is
    represented by this model
    """
    result = models.ForeignKey(Result, verbose_name="Result",
                               help_text="Result of scan", on_delete=models.CASCADE)
    state = models.PositiveIntegerField(
        default=RESULT_GROUP_STATES["UNKNOWN"],
        choices=RESULT_GROUP_STATES.get_mapping(),
        help_text="Type of waiver")
    checker_group = models.ForeignKey(CheckerGroup,
                                      verbose_name="Group of checkers", on_delete=models.CASCADE)
    defect_type = models.PositiveIntegerField(
        default=DEFECT_STATES["UNKNOWN"],
        choices=DEFECT_STATES.get_mapping(),
        help_text="Type of defects that are associated with this group.")
    defects_count = models.PositiveSmallIntegerField(
        default=0, blank=True, null=True, verbose_name="Number of defects \
associated with this group.")

    objects = ResultGroupManager()

    def __str__(self):
        return "#%d [%s - %s], Result: (%s)" % (
            self.id, self.checker_group.name, self.get_state_display(),
            self.result
        )

    def has_fix_later_waiver(self):
        """ is waiver associated with this rg fix later? """
        w = self.has_waiver()
        return w and w.is_fix_later()

    def is_waived(self):
        return self.state == RESULT_GROUP_STATES['WAIVED']

    def contains_bug(self):
        return self.state == RESULT_GROUP_STATES['CONTAINS_BUG']

    def is_previously_waived(self):
        return self.state == RESULT_GROUP_STATES['PREVIOUSLY_WAIVED'] or \
            self.defect_type == DEFECT_STATES['PREVIOUSLY_WAIVED']

    def get_new_defects(self):
        return Defect.objects.filter(result_group=self.id,
                                     state=DEFECT_STATES['NEW'])

    def get_waivers(self):
        """return all non-deleted waivers associated with this rg"""
        return Waiver.waivers.waivers_for(self)

    def latest_waiver(self):
        waivers = self.get_waivers()
        if waivers:
            return waivers.latest()

    def has_waiver(self):
        """
        return latest waiver, if it exists
        """
        if self.state in RESULT_GROUP_PROCESSED:
            return self.latest_waiver()

    def is_marked_as_bug(self):
        """
        return True if there is latest waiver with type IS_A_BUG
        """
        # new style
        if self.contains_bug():
            return True
        # old style
        w = self.has_waiver()
        if w:
            return w.is_bug()
        else:
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
        elif self.defect_type == DEFECT_STATES["NEW"] or \
                self.defect_type == DEFECT_STATES["PREVIOUSLY_WAIVED"]:
            if self.defects_count > 0:
                if self.is_marked_as_bug() and self.is_waived():
                    return 'IS_A_BUG'
                elif self.has_fix_later_waiver():
                    return 'FIX_LATER'
                else:
                    return self.get_state_display()
            else:
                return 'PASSED'

    def previous_waivers(self):
        """Return every past waiver associated with this rg"""
        actual_waivers = Waiver.objects.filter(result_group=self)
        if actual_waivers:
            d = actual_waivers.order_by('date')[0].date
        else:
            d = self.result.date_submitted
        w = Waiver.objects.filter(
            result_group__checker_group=self.checker_group,
            date__lt=d,
            result_group__result__scanbinding__scan__package=self.result.scanbinding.scan.package
        )
        if w:
            return w.order_by('-date')

    def waive(self, save=True):
        self.state = RESULT_GROUP_STATES['WAIVED']
        if save:
            self.save()

    def set_bug_confirmed(self, save=True):
        self.state = RESULT_GROUP_STATES['CONTAINS_BUG']
        if save:
            self.save()

    def apply_waiver(self, waiver):
        if waiver.is_bug():
            self.set_bug_confirmed()
        else:
            self.waive()


class Checker(models.Model):
    """
    Checker is a type of defect.
    """
    name = models.CharField("Checker's name", max_length=64,
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
checker belong", on_delete=models.CASCADE)

    def __str__(self):
        return "#%d %s, CheckerGroup: (%s)" % (self.id, self.name, self.group)


class Bug(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    release = models.ForeignKey(SystemRelease, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class JiraBug(Bug):
    key = models.CharField(max_length=64)

    def __str__(self):
        return "#%d Jira Issue #%s (%s, %s.%d)" % (
            self.id,
            self.key,
            self.package.name,
            self.release.product,
            self.release.release,
        )


class Bugzilla(Bug):
    number = models.IntegerField()

    def __str__(self):
        return "#%d BZ#%d (%s, %s.%d)" % (
            self.id,
            self.number,
            self.package.name,
            self.release.product,
            self.release.release,
        )


class WaiverOnlyMixin:
    def by_release(self, release):
        return self.filter(
            result_group__result__scanbinding__scan__tag__release=release)

    def by_package(self, package):
        return self.filter(
            result_group__result__scanbinding__scan__package=package)

    def unreported(self, model):
        model_name = model.__name__
        if model_name.lower() == 'bugzilla':
            field = 'bz'
        elif model_name.lower() == 'jirabug':
            field = 'jira_bug'
        else:
            raise ValueError(f"Unknown model_name: {model_name}")
        query = f"{field}__isnull"
        return self.filter(**{query: True})

    def waivers_for(self, rg):
        return self.filter(result_group=rg)

    def updates(self):
        """ return all waivers for regular updates """
        return self.filter(
            result_group__result__scanbinding__scan__scan_type=SCAN_TYPES['ERRATA'])

    def newpkgs(self):
        """ return all waivers for newpkgs """
        return self.filter(
            result_group__result__scanbinding__scan__scan_type=SCAN_TYPES['NEWPKG'])

    def rebases(self):
        """ return all waivers for rebases """
        return self.filter(
            result_group__result__scanbinding__scan__scan_type=SCAN_TYPES['REBASE'])

    def is_a_bugs(self):
        return self.filter(state=WAIVER_TYPES["IS_A_BUG"])

    def not_a_bugs(self):
        return self.filter(state=WAIVER_TYPES["NOT_A_BUG"])

    def fix_laters(self):
        return self.filter(state=WAIVER_TYPES["FIX_LATER"])


class WaiverOnlyQuerySet(models.query.QuerySet, WaiverOnlyMixin):
    pass


class WaiverOnlyManager(models.Manager, WaiverOnlyMixin):
    def get_queryset(self):
        """ return all active waivers """
        return WaiverOnlyQuerySet(self.model, using=self._db).filter(is_deleted=False).filter(is_active=True)


class WaiverManager(models.Manager):
    pass


class Waiver(models.Model):
    """
    User acknowledges that he processed associated defect group
    """
    date = models.DateTimeField(auto_now_add=True)  # date submitted
    message = models.TextField("Message")
    result_group = models.ForeignKey(ResultGroup, blank=False, null=False,
                                     help_text="Group of defects which is \
waived for specific Result", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    state = models.PositiveIntegerField(default=WAIVER_TYPES["IS_A_BUG"],
                                        choices=WAIVER_TYPES.get_mapping(),
                                        help_text="Type of waiver")
    bz = models.ForeignKey(Bugzilla, blank=True, null=True, on_delete=models.CASCADE)
    jira_bug = models.ForeignKey(JiraBug, blank=True, null=True, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)

    is_active = models.BooleanField(default=False)

    objects = WaiverManager()
    waivers = WaiverOnlyManager()

    class Meta:
        get_latest_by = "date"
        ordering = ("-date", )

    def __str__(self):
        return "#%d %s - %s, ResultGroup: (%s) BZ: %s" % (
            self.id,
            self.message,
            self.get_state_display(),
            self.result_group,
            self.bz
        )

    def is_comment(self):
        return self.state == WAIVER_TYPES['COMMENT']

    def is_not_a_bug(self):
        """ does this waiver has type 'not a bug'? """
        return self.state == WAIVER_TYPES['NOT_A_BUG']

    def is_bug(self):
        """ type == 'is a bug' """
        return self.state == WAIVER_TYPES['IS_A_BUG']

    def is_fix_later(self):
        return self.state == WAIVER_TYPES['FIX_LATER']

    def marks_bug(self):
        """ this waiver marks bug: either 'fix later' or 'is a bug' """
        return self.is_bug() or self.is_fix_later()

    def type_text(self):
        if self.is_comment():
            return "Comment"
        else:
            return "Waiver"

    def get_display_type(self):
        return WAIVER_TYPES.get_item_help_text(self.state)

    def get_delete_waiving_log(self):
        return WaivingLog.objects.get(
            waiver=self,
            state=WAIVER_LOG_ACTIONS['DELETE']
        )

    @classmethod
    def new_comment(cls, text, rg, user):
        return cls(message=text, result_group=rg,
                   user=user, state=WAIVER_TYPES['COMMENT'])


class WaivingLogMixin:
    def not_deleted(self):
        return self.exclude(state=WAIVER_LOG_ACTIONS['DELETE'])

    def for_rg(self, rg_id):
        return self.not_deleted().filter(waiver__result_group=rg_id)

    def for_waiver(self, waiver):
        return self.not_deleted().filter(waiver=waiver)


class WaivingLogQuerySet(models.query.QuerySet, WaivingLogMixin):
    pass


class WaivingLogManager(models.Manager, WaivingLogMixin):
    def get_queryset(self):
        """ return all active waivers """
        return WaivingLogQuerySet(self.model, using=self._db)


class WaivingLog(models.Model):
    """
    Log of waiving related actions
    """
    date = models.DateTimeField(auto_now_add=True)  # date submitted
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # possible actions:
    #  new -- submit waiver to group that wasn't waived yet
    #  delete -- delete waiver
    #  rewaive -- submit another waiver
    state = models.PositiveIntegerField(
        choices=WAIVER_LOG_ACTIONS.get_mapping(),
        help_text="Waiving action"
    )
    waiver = models.ForeignKey(Waiver, on_delete=models.CASCADE)

    objects = WaivingLogManager()

    class Meta:
        ordering = ['date']

    def __str__(self):
        return "#%d %s (%s)" % (
            self.id,
            WAIVER_LOG_ACTIONS.get_value(self.state),
            self.waiver,
        )

    @classmethod
    def new_log(cls, user, waiver=None):
        if waiver:
            return cls(state=WAIVER_LOG_ACTIONS['NEW'], user=user,
                       waiver=waiver)
        else:
            return cls(state=WAIVER_LOG_ACTIONS['NEW'], user=user)
