# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import datetime
import json
import logging
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import (MultipleObjectsReturned,
                                    ObjectDoesNotExist, ValidationError)
from django.db import models, transaction
from django.urls import reverse
from django.utils.safestring import mark_safe
from kobo.client.constants import TASK_STATES
from kobo.hub.models import Task
from kobo.types import Enum, EnumItem

from osh.hub.other import get_or_none
from osh.hub.scan.messaging import post_qpid_message

logger = logging.getLogger(__name__)


SCAN_STATES = Enum(
    "QUEUED",            # scan was submitted, waiting for scheduler
    "SCANNING",          # scan/task is active now
    "NEEDS_INSPECTION",  # scan finished and there are defects which need
                         #  owner's attention
    "WAIVED",            # user appropriately waived each defect
    "PASSED",            # scan didn't discover new defects; everything is fine
    "FINISHED",          # scan finished -- USER/ERRATA_BASE scans only
    "FAILED",            # scan has failed, need an attention by OpenScanHub admins
                         #  (something went wrong during build process or
                         #  analyser had some problems)
    "BASE_SCANNING",     # child scan is in scanning process right now
    "CANCELED",          # there is newer build submitted, this one is obsolete
    "DISPUTED",          # scan was waived but one of waivers was obsoleted
    "INIT",              # first, default state
    "BUG_CONFIRMED",     # run contains at least one group marked as bug
)

SCAN_STATES_IN_PROGRESS = (
    SCAN_STATES['QUEUED'],
    SCAN_STATES['SCANNING'],
    SCAN_STATES['BASE_SCANNING'],
    SCAN_STATES['INIT'],
)
SCAN_STATES_FINISHED = (
    SCAN_STATES['NEEDS_INSPECTION'],
    SCAN_STATES['WAIVED'],
    SCAN_STATES['PASSED'],
    SCAN_STATES['FAILED'],
    SCAN_STATES['CANCELED'],
    SCAN_STATES['DISPUTED'],
    SCAN_STATES['BUG_CONFIRMED'],
)
SCAN_STATES_FINISHED_WELL = (
    SCAN_STATES['NEEDS_INSPECTION'],
    SCAN_STATES['WAIVED'],
    SCAN_STATES['PASSED'],
    SCAN_STATES['DISPUTED'],
    SCAN_STATES['BUG_CONFIRMED'],
)
SCAN_STATES_FINISHED_BAD = (
    SCAN_STATES['FAILED'],
    SCAN_STATES['CANCELED'],
)
SCAN_STATES_BASE = (
    SCAN_STATES['FINISHED'],
)
SCAN_STATES_PROCESSED = (
    SCAN_STATES['PASSED'],
    SCAN_STATES['WAIVED'],
)
SCAN_STATES_SEND_MAIL = (
    SCAN_STATES['NEEDS_INSPECTION'],
    SCAN_STATES['FAILED'],
)

SCAN_TYPES = Enum(
    # regular ET scan (not rebase, not new pkg, etc.)
    EnumItem("ERRATA", help_text="Regular"),
    # base scan (this is basicly just mock build)
    EnumItem("ERRATA_BASE", help_text="Base Scan"),
    # some user posted this scan (for future)
    EnumItem("USER", help_text="User Scan"),
    # base.nvr.version != target.nvr.version
    EnumItem("REBASE", help_text="Rebase"),
    # just an informational mock build; base == None
    EnumItem("NEWPKG", help_text="New Package"),
)

SCAN_TYPES_TARGET = (
    SCAN_TYPES['ERRATA'],
    SCAN_TYPES['REBASE'],
    SCAN_TYPES['NEWPKG'],
)

REQUEST_STATES = Enum(
    EnumItem("OK", help_text="Ok"),
    EnumItem("ERROR", help_text="An unexpected error happened"),
    EnumItem("INELIGIBLE", help_text="Package is not eligible for scanning"),
)


class Permissions(models.Model):
    """
    Custom permissions
    """
    class Meta:
        permissions = (
            ('errata_xmlrpc_scan',
             'Can submit ET scan via XML-RPC'),
        )


class MockConfigMixin:
    def verify_by_name(self, name):
        try:
            model = self.get(name=name)
        except ObjectDoesNotExist:
            logger.warning("Mock config %s does not exist", name)
            raise
        else:
            if not model.enabled:
                raise RuntimeError('Mock config %s is disabled', model)
            return model


class MockConfigQuerySet(models.query.QuerySet, MockConfigMixin):
    pass


class MockConfigManager(models.Manager, MockConfigMixin):
    def get_queryset(self):
        return MockConfigQuerySet(self.model, using=self._db)


class MockConfig(models.Model):
    name = models.CharField(max_length=256, unique=True)
    enabled = models.BooleanField(default=True)

    objects = MockConfigManager()

    class Meta:
        ordering = ("name", )

    def __str__(self):
        return self.name

    def export(self):
        result = {
            "name": self.name,
            "enabled": self.enabled,
        }
        return result


class SystemReleaseMixin:
    def active(self):
        return self.filter(active=True)


class SystemReleaseQuerySet(models.query.QuerySet, SystemReleaseMixin):
    pass


class SystemReleaseManager(models.Manager, SystemReleaseMixin):
    def get_queryset(self):
        return SystemReleaseQuerySet(self.model, using=self._db)


class SystemRelease(models.Model):
    """
    Represents release for which are scans submitted
    """
    # rhel-6.4 | rhel-7 etc.
    tag = models.CharField("Short tag", max_length=16, blank=False)

    # Red Hat Enterprise Linux 6 etc.
    product = models.CharField("Product name", max_length=128, blank=False)

    # release number (y) -- RHEL-x.y
    release = models.IntegerField()

    active = models.BooleanField(default=True, help_text="If set to True,\
statistical data will be harvested for this system release.")

    parent = models.OneToOneField("self", on_delete=models.CASCADE, blank=True, null=True)

    objects = SystemReleaseManager()

    def __str__(self):
        return "%s -- %s.%d" % (self.tag, self.product, self.release)

    @property
    def child(self):
        try:
            return self.systemrelease
        except ObjectDoesNotExist:
            return None

    def is_parent(self):
        return self.child is not None

    @property
    def version(self):
        """
        Product release numbers (major.minor)
        """
        digits = re.search(r'(\d)', self.product)
        assert digits is not None, f'Unable to parse major version from: {self.product!r}'
        x = digits.group(1)
        y = self.release
        return f"{x}.{y}"


class TagMixin:
    def for_release_str(self, release_str):
        for rm in ReleaseMapping.objects.all():
            tag = rm.get_tag(release_str)
            if tag:
                return tag
        logger.critical("Unable to assign proper product and release: %s", release_str)
        raise RuntimeError("Packages in this release are not being scanned.")


class TagQuerySet(models.query.QuerySet, TagMixin):
    pass


class TagManager(models.Manager, TagMixin):
    def get_queryset(self):
        return TagQuerySet(self.model, using=self._db)


class Tag(models.Model):
    """
    Mapping between brew tags and mock configs
    """

    name = models.CharField("Brew Tag", max_length=64, blank=False)
    mock = models.ForeignKey(MockConfig, verbose_name="Mock Config",
                             blank=False, null=False,
                             related_name='mock_profile', on_delete=models.CASCADE)
    release = models.ForeignKey(SystemRelease, related_name='system_release', on_delete=models.CASCADE)

    objects = TagManager()

    def __str__(self):
        return "Tag: %s --> Mock: %s (%s)" % \
            (self.name, self.mock, self.release)


class PackageMixin:
    def get_or_create_by_name(self, name):
        model, created = self.get_or_create(name=name)
        return model


class PackageQuerySet(models.query.QuerySet, PackageMixin):
    pass


class PackageManager(models.Manager, PackageMixin):
    def get_queryset(self):
        return PackageQuerySet(self.model, using=self._db)


class Package(models.Model):
    """
    model that represents packages, these are linked directly to scans
    """
    name = models.CharField("Package name", max_length=64,
                            blank=False, null=False)
    blocked = models.BooleanField(default=False, help_text="If this is set to \
True, the package is blocked -- not accepted for scanning.", blank=True, null=True)
    priority_offset = models.SmallIntegerField(default=0, help_text="Set this to alter priority \
of this packages scan")

    objects = PackageManager()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return "#%s %s" % (self.id, self.name)

    def calculateScanNumbers(self):
        return Scan.objects.filter(package=self,
                                   scan_type__in=SCAN_TYPES_TARGET).count()

    scans_number = property(calculateScanNumbers)

    def get_latest_scans(self):
        srs = SystemRelease.objects.filter(active=True)
        response = ""
        for sr in srs:
            scans = Scan.objects.filter(package=self, tag__release=sr,
                                        enabled=True)
            if scans:
                scan = scans.latest()
                response += '%s: <a href="%s">%s</a>, ' % (
                    sr.tag,
                    reverse("waiving/result/newest", args=(self.name, sr.tag)),
                    scan.nvr,
                )
        if response == "":
            return "None"
        else:
            return mark_safe(response[:-2])

    display_latest_scans = property(get_latest_scans)

    def display_graph(self, scan, response, indent_level=0):
        if scan is None:
            return response
        sb = ScanBinding.objects.get(scan=scan)

        response += '<div style="margin-left: %dem">%s<a href="%s">%s</a> (%s)' % (
            indent_level if indent_level <= 1 else indent_level * 2,
            '\u2570\u2500\u2500' if indent_level > 0 else '',
            reverse("waiving/result", args=(sb.id,)),  # url
            scan.nvr,
            scan.get_state_display())

        if sb.result is not None:
            response += ' New defects: %d, fixed defects: %d' % (
                sb.result.new_defects_count(),
                sb.result.fixed_defects_count())

        response += '</div>\n'

        return self.display_graph(scan.parent,
                                  response, indent_level + 1)

    def display_scan_tree(self):
        blocked_releases = self.get_partially_blocked_releases()\
                               .values_list('release', flat=True)
        scans = Scan.objects.filter(package=self)

        if not blocked_releases and not scans:
            return mark_safe('There are no scans submitted related to this \
package')

        releases = scans.filter(tag__release__isnull=False)\
                        .values_list('tag__release', flat=True)\
                        .union(blocked_releases)
        response = ""

        for release_id in sorted(releases):
            scans_package = scans.filter(
                tag__release__id=release_id,
                state__in=SCAN_STATES_FINISHED_WELL,
                scan_type__in=SCAN_TYPES_TARGET)

            release = SystemRelease.objects.get(id=release_id)

            response += '<div>\n<div style="display:flex; align-items: center;">\n'
            response += '<h3>%s release %d%s</h3>\n' % (
                release.product,
                release.release,
                ' &ndash; BLOCKED' if release_id in blocked_releases else ''
            )

            if not scans_package:
                response += "</div>No successful scans in this release.<hr/ ></div>\n"
                continue

            # get latest scan with the first NVR
            first_nvr = scans_package.order_by('date_submitted')[0].nvr
            first_scan = scans_package.filter(nvr=first_nvr).latest()

            # handle base scan
            base = first_scan.base
            response += '<span style="position:absolute; left: 45em">Base: '

            if base is not None:
                sb_base = ScanBinding.objects.get(scan=base)
                response += '<a href="%s">%s</a>' % (
                    reverse("waiving/result", args=(sb_base.id,)),
                    base.nvr)
            else:
                response += 'NEW PACKAGE'

            response += '</span>\n</div>\n'

            response = self.display_graph(first_scan, response)
            response += "<hr/ ></div>\n"
        return mark_safe(response)

    def is_blocked(self, release):
        try:
            atr = PackageAttribute.blocked(self, release)
        except ObjectDoesNotExist:
            return self.blocked
        else:
            return atr.is_blocked()

    def get_partially_blocked_releases(self):
        return PackageAttribute.objects.filter(
            package=self, key=PackageAttribute.BLOCKED, value='Y').values('release')

    def get_priority_offset(self):
        return int(self.priority_offset)


class PackageAttributeMixin:
    def by_package(self, package):
        return self.filter(package=package)

    def by_release(self, release):
        return self.filter(release=release)


class PackageAttributeQuerySet(models.query.QuerySet, PackageAttributeMixin):
    pass


class PackageAttributeManager(models.Manager, PackageAttributeMixin):
    def get_queryset(self):
        return PackageAttributeQuerySet(self.model, using=self._db)

    def get_blocked_packages(self):
        return self.get_queryset().filter(key=PackageAttribute.BLOCKED, value='Y').values_list("package__id", flat=True)


class PackageAttribute(models.Model):
    """
    keys:
    BLOCKED: {Y | N}
     * If this is set to True, the package is blocked -- not accepted
    for scanning.
    """
    BLOCKED = 'BLOCKED'

    key = models.CharField(max_length=64, null=True, blank=True)
    value = models.CharField(max_length=128, null=True, blank=True)
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    release = models.ForeignKey(SystemRelease, on_delete=models.CASCADE)

    objects = PackageAttributeManager()

    def __str__(self):
        return "%s = %s (%s %s)" % (self.key, self.value, self.package, self.release)

    @classmethod
    def create(cls, package, release):
        atr = cls()
        atr.release = release
        atr.package = package
        return atr

    @classmethod
    def _get_for_package_in_release(cls, package, release, key=None):
        """
        return package attribute for provided package/release
        """
        if key:
            return cls.objects.get(package=package, release=release, key=key)
        else:
            return cls.objects.get(package=package, release=release)

    @classmethod
    def blocked(cls, package, release):
        return cls._get_for_package_in_release(package, release, PackageAttribute.BLOCKED)

    def _is(self, key, exc_type):
        if self.key == key:
            return self.value == 'Y'
        else:
            raise ValueError('This attribute (%s) is not related to %s stuff.'
                             % (self.key, exc_type))

    def is_blocked(self):
        return self._is(PackageAttribute.BLOCKED, 'blocked')

    @classmethod
    def create_new_bool(cls, package, release, key, value):
        bool_value = 'Y' if value else 'N'
        atr = cls.create(package, release)
        atr.key = key
        atr.value = bool_value
        atr.save()
        return atr

    @classmethod
    def create_blocked(cls, package, release, blocked):
        return cls.create_new_bool(package, release, PackageAttribute.BLOCKED, blocked)


class ScanMixin:
    def by_release(self, release):
        return self.filter(tag__release=release)

    def target(self):
        return self.filter(scan_type__in=SCAN_TYPES_TARGET)

    def enabled(self):
        return self.filter(enabled=True)

    def updates(self):
        return self.enabled().filter(scan_type=SCAN_TYPES['ERRATA'])

    def newpkgs(self):
        return self.enabled().filter(scan_type=SCAN_TYPES['NEWPKG'])

    def rebases(self):
        return self.enabled().filter(scan_type=SCAN_TYPES['REBASE'])


class ScanQuerySet(models.query.QuerySet, ScanMixin):
    pass


class ScanManager(models.Manager, ScanMixin):
    def get_queryset(self):
        return ScanQuerySet(self.model, using=self._db)


class ScanTargetMixin:
    pass


class ScanTargetQuerySet(models.query.QuerySet, ScanTargetMixin):
    pass


class ScanTargetManager(models.Manager, ScanTargetMixin):
    def get_queryset(self):
        return ScanTargetQuerySet(self.model, using=self._db).filter(scan_type__in=SCAN_TYPES_TARGET)


class Scan(models.Model):
    """
    Stores information about submitted scans from Errata Tool
    """
    # yum-3.4.3-42.el7
    nvr = models.CharField("NVR", max_length=512,
                           blank=False, help_text="Name-Version-Release")

    scan_type = models.PositiveIntegerField(default=SCAN_TYPES["ERRATA"],
                                            choices=SCAN_TYPES.get_mapping(),
                                            help_text="Scan Type")

    state = models.PositiveIntegerField(default=SCAN_STATES["INIT"],
                                        choices=SCAN_STATES.get_mapping(),
                                        help_text="Current scan state")

    # information for differential scan -- which version of package we are
    # diffing to
    base = models.ForeignKey('self', verbose_name="Base Scan",
                             blank=True, null=True,
                             help_text="NVR of package to diff against",
                             related_name="base_scan", on_delete=models.CASCADE)
    # user scans dont have to specify this option -- allow None
    tag = models.ForeignKey(Tag, verbose_name="Tag",
                            blank=True, null=True,
                            help_text="Tag from brew", on_delete=models.CASCADE)

    username = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # date when there was last access to scan
    # should change when:
    #   - scan has finished
    #   - waiver added
    #   - waiver invalidated
    last_access = models.DateTimeField(blank=True, null=True)

    date_submitted = models.DateTimeField(auto_now_add=True)

    enabled = models.BooleanField(default=True, help_text="This scan is \
counted in statistics.")

    package = models.ForeignKey(Package, on_delete=models.CASCADE)

    parent = models.ForeignKey('self', verbose_name="Parent Scan", blank=True,
                               null=True, related_name="parent_scan", on_delete=models.CASCADE)

    objects = ScanManager()
    targets = ScanTargetManager()

    class Meta:
        get_latest_by = "date_submitted"

    def __str__(self):
        prefix = "#%s %s %s" % (self.id,
                                self.nvr,
                                self.get_state_display())
        if self.base:
            return "%s Base: %s" % (prefix, self.base.nvr)
        else:
            return prefix

    def can_have_base(self):
        return self.scan_type in (SCAN_TYPES['ERRATA'], SCAN_TYPES['REBASE'])

    def is_rebase_scan(self):
        return self.scan_type == SCAN_TYPES['REBASE']

    def is_newpkg_scan(self):
        return self.scan_type == SCAN_TYPES['NEWPKG']

    def is_errata_scan(self):
        return self.scan_type in SCAN_TYPES_TARGET

    def is_errata_base_scan(self):
        return self.scan_type == SCAN_TYPES['ERRATA_BASE']

    def is_user_scan(self):
        return self.scan_type == SCAN_TYPES['USER']

    def is_waived(self):
        return self.state == SCAN_STATES['WAIVED']

    def is_failed(self):
        return self.state == SCAN_STATES['FAILED']

    def is_canceled(self):
        return self.state == SCAN_STATES['CANCELED']

    def is_disputed(self):
        return self.state == SCAN_STATES['DISPUTED']

    def is_in_progress(self):
        return self.state in SCAN_STATES_IN_PROGRESS

    @property
    def target(self):
        if self.is_errata_base_scan():
            return self.scanbinding.task.parent.scanbinding.scan

    @property
    def overdue(self):
        """
        Return CSS class name if scan's overdue state -- not waived on time
        """
        if self.waived_on_time() is False:
            return "red_font"
        else:
            return ""

    def waived_on_time(self):
        """
        either scan is processed (passed/waived) or user still has time to
        process it

        Return:
            - None -- scan does not need to be waived
            - True -- processed on time/still has time to process it
            - False -- do not processed on time
        """
        if self.state in SCAN_STATES_FINISHED_BAD:
            return None

        d = AppSettings.setting_waiver_is_overdue()
        return self.state in SCAN_STATES_PROCESSED or \
            self.last_access > datetime.datetime.now() - \
            datetime.timedelta(days=d)

    @classmethod
    def create_scan(cls, scan_type, nvr, username, package,
                    enabled, base=None, tag=None):
        scan = cls()
        scan.scan_type = scan_type
        scan.nvr = nvr
        scan.base = base
        scan.tag = tag
        scan.username = get_user_model().objects.get_or_create(username=username)[0]
        scan.last_access = datetime.datetime.now()
        scan.package = package
        scan.enabled = enabled
        scan.save()
        return scan

    def clone_scan(self, base=None):
        scan = Scan()
        scan.scan_type = self.scan_type
        scan.nvr = self.nvr
        scan.tag = self.tag
        if self.is_errata_base_scan():
            scan.base = None
            scan.enabled = False
        else:
            scan.enabled = True
            # base shouldn't be None
            # I'm not adding get_latest_binding here because of reference lock
            scan.base = base
        scan.username = self.username
        scan.last_access = datetime.datetime.now()
        scan.package = self.package
        scan.save()
        return scan

    def scan_state_notice(self):
        if self.state in SCAN_STATES_IN_PROGRESS:
            key = 'unfinished'
        else:
            key = 'finished'
        if self.is_errata_base_scan():
            return
        if AppSettings.setting_send_bus_message():
            post_qpid_message(
                SCAN_STATES.get_value(self.state),
                ETMapping.objects.get(latest_run=self.scanbinding),
                key
            )

    def set_base(self, base, save=True):
        self.base = base
        if save:
            self.save()

    def set_state(self, state):
        if state == self.state:
            return
        self.state = state
        self.save()
        self.scan_state_notice()

    def set_state_scanning(self):
        self.set_state(SCAN_STATES['SCANNING'])

    def set_state_basescanning(self):
        self.set_state(SCAN_STATES['BASE_SCANNING'])

    def set_state_queued(self):
        self.set_state(SCAN_STATES['QUEUED'])

    def set_state_bug_confirmed(self):
        self.set_state(SCAN_STATES['BUG_CONFIRMED'])

    def get_child_scan(self):
        try:
            return Scan.objects.get(parent=self)
        except ObjectDoesNotExist:
            return None

    def get_first_scan_binding(self):
        if self.tag is None:
            return None

        related_scans = ScanBinding.objects.filter(
            scan__package=self.package,
            scan__tag__release=self.tag.release,
            task__state=TASK_STATES['CLOSED'],
            scan__scan_type__in=SCAN_TYPES_TARGET).\
            order_by('result__date_submitted')
        if related_scans:
            return related_scans[0]
        else:
            return None

    def enable_last_successfull(self):
        last_finished = self
        while last_finished:
            if last_finished.state in SCAN_STATES_FINISHED_WELL:
                last_finished.enabled = True
                last_finished.save()
                break
            last_finished = last_finished.get_child_scan()

    def all_scans_in_release(self):
        if self.tag is None:
            return Scan.objects.none()

        scans = Scan.objects.filter(
            package=self.package,
            tag__release=self.tag.release
        ).exclude(
            state__in=SCAN_STATES_FINISHED_BAD
        ).order_by('date_submitted')
        return scans

    def finalize(self):
        """
        this scan doesn't contain any unprocessed defects
        let's finalize it!
        """
        if self.scanbinding.result.has_bugs():
            self.set_state(SCAN_STATES['BUG_CONFIRMED'])
        else:
            self.set_state(SCAN_STATES['WAIVED'])
        self.save()


class ScanBindingMixin:
    def latest_packages_scans(self):
        return self.finished_well().filter(scan__parent=None)

    def overdue_scans(self):
        # exclude waived or incomplete scans
        nonwaivable_states = SCAN_STATES_PROCESSED + SCAN_STATES_FINISHED_BAD
        waivable_scans = self.exclude(scan__state__in=nonwaivable_states)

        # filter overdue scans
        d = AppSettings.setting_waiver_is_overdue()
        grace_period = datetime.datetime.now() - datetime.timedelta(days=d)
        return waivable_scans.filter(scan__last_access__lte=grace_period)

    def by_scan_id(self, scan_id):
        return self.get(scan__id=scan_id)

    def by_package(self, package):
        return self.filter(scan__package=package)

    def by_release(self, release):
        return self.filter(scan__tag__release=release)

    def by_package_name(self, package_name):
        return self.filter(scan__package__name=package_name)

    def by_release_name(self, release_name):
        return self.filter(scan__tag__release__tag=release_name)

    def enabled(self):
        return self.filter(scan__enabled=True)

    def target(self):
        return self.filter(scan__scan_type__in=SCAN_TYPES_TARGET)

    def rebases(self):
        return self.filter(scan__scan_type=SCAN_TYPES['REBASE'])

    def updates(self):
        return self.filter(scan__scan_type=SCAN_TYPES['ERRATA'])

    def newpkgs(self):
        return self.filter(scan__scan_type=SCAN_TYPES['NEWPKG'])

    def latest_scan_of_package(self, package, release):
        """ return latest scan of package in specific release """
        q = self.target().by_release(release).by_package(package).finished_well()
        if q:
            return q.latest()

    def finished_well(self):
        return self.filter(scan__state__in=SCAN_STATES_FINISHED_WELL)


class ScanBindingQuerySet(models.query.QuerySet, ScanBindingMixin):
    pass


class ScanBindingManager(models.Manager, ScanBindingMixin):
    def get_queryset(self):
        return ScanBindingQuerySet(self.model, using=self._db)


class TargetScanBindingManager(models.Manager, ScanBindingMixin):
    def get_queryset(self):
        return ScanBindingQuerySet(self.model, using=self._db).filter(scan__scan_type__in=SCAN_TYPES_TARGET)


class ScanBinding(models.Model):
    """
    Binding between scan, task and result -- for easier creation of scans that
    are already submitted
    """
    task = models.OneToOneField(Task, verbose_name="Asociated Task",
                                help_text="Asociated task on worker",
                                on_delete=models.CASCADE, blank=True, null=True,)
    scan = models.OneToOneField(Scan, on_delete=models.CASCADE,
                                verbose_name="Scan")
    result = models.OneToOneField("waiving.Result", on_delete=models.CASCADE,
                                  blank=True, null=True,)

    objects = ScanBindingManager()

    targets = TargetScanBindingManager()

    class Meta:
        get_latest_by = "result__date_submitted"

    def __str__(self):
        return "#%d: Scan: %s | %s" % (self.id, self.scan, self.task)

    @classmethod
    def create_sb(cls, **kwargs):
        instance = cls(**kwargs)
        instance.save()
        return instance

    def get_errata_id(self):
        if self.is_errata_scan():
            try:
                return ETMapping.objects.get(latest_run=self).et_scan_id
            except KeyError:
                return None
        return None

    def analyzers_match(self, analyzers):
        """ list of dicts with info about analyzers """
        if not self.result:
            return False
        sb_analyzers = self.result.analyzers.all()
        # FIXME: this will not detect equally sized sets of non-matching items
        if len(analyzers) != len(sb_analyzers):
            logger.info("Analyzer sets don't match: %s != %s", analyzers, sb_analyzers)
            return False
        for a in analyzers:
            for sb_a in sb_analyzers:
                if a.analyzer.name == sb_a.analyzer.name:
                    # FIXME: move this list to the database to ease updates
                    if a.analyzer.name in ["gcc", "gcc-analyzer", "clang"]:
                        # version of gcc/clang is not under our control anyway
                        break
                    if not a.version == sb_a.version:
                        logger.info("%s-%s != %s-%s", a.analyzer.name, a.version,
                                    sb_a.analyzer.name, sb_a.version)
                        # one of the version doesn't match
                        return False
                    else:
                        # continue with another analyzer
                        break
        return True

    def is_actual(self, mock_config):
        """ is scan actual? ~ scanned with up to date analyzers """
        analyzers = AnalyzerVersion.objects.get_analyzer_versions_for_mockprofile(mock_config)
        logger.info("Analyzer versions in mock profile %s: %s", mock_config, analyzers)
        return self.analyzers_match(analyzers)


class ReleaseMapping(models.Model):
    # regular expression
    release_tag = models.CharField(max_length=32, blank=False, null=False)
    # string template for inserting values gathered through regex
    # "RHEL-%s.%s" % re.match(self.release_tag, ...).groups()
    template = models.CharField(max_length=32, blank=False, null=False)
    priority = models.IntegerField()

    class Meta:
        ordering = ['priority']

    def __str__(self):
        return "#%d (%d) %s %s" % (self.id, self.priority,
                                   self.release_tag, self.template)

    def get_tag(self, rhel_version):
        logger.debug("Getting tag for %s" % rhel_version)
        m = re.match(self.release_tag, rhel_version)
        if m:
            try:
                tag = Tag.objects.get(name=self.template % m.groups())
            except ObjectDoesNotExist:
                return
            except MultipleObjectsReturned:
                return
            else:
                return tag


class ETMapping(models.Model):
    advisory_id = models.CharField(max_length=16, blank=False, null=False)
    et_scan_id = models.CharField(max_length=16, blank=False, null=False)
    latest_run = models.ForeignKey(ScanBinding, null=True, blank=True, on_delete=models.CASCADE)
    comment = models.CharField(max_length=384, default="", blank=True)
    state = models.PositiveIntegerField(
        default=REQUEST_STATES['OK'],
        choices=REQUEST_STATES.get_mapping(),
        help_text="Status of request"
    )

    def __str__(self):
        return "#%d Advisory: %s %s" % (self.id, self.advisory_id,
                                        self.latest_run)

    def set_latest_run(self, sb, save=True):
        self.latest_run = sb
        if save:
            self.save()


class AppSettings(models.Model):
    """
    Settings for OpenScanHub stored in DB so they can be easily changed.

    SEND_EMAIL { Y, N }
    SEND_BUS_MESSAGE { Y, N }

    CHECK_USER_CAN_SUBMIT_SCAN { Y, N }

    WAIVER_IS_OVERDUE int

    SCANNING_COMMAND_RELSPEC -- override of default
    """
    key = models.CharField(max_length=128, blank=False, null=False)
    value = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "AppSettings"

    def __str__(self):
        return "%s = %s" % (self.key, self.value)

    @classmethod
    def setting_send_mail(cls):
        """Should hub send mails when scan finishes?"""
        return cls.objects.get(key="SEND_MAIL").value.upper() == "Y"

    @classmethod
    def setting_send_bus_message(cls):
        """Should hub post messages to bus whenever scan's state changes?"""
        return cls.objects.get(key="SEND_BUS_MESSAGE").value.upper() == "Y"

    @classmethod
    def setting_check_user_can_submit(cls):
        """
        Should hub check whether user is permit to submit scan?
         "Y" => hub has to check user perm 'scan.errata_xmlrpc_scan'
         "N" => hub does not have to check
        """
        return cls.objects.get(key="CHECK_USER_CAN_SUBMIT_SCAN").\
            value.upper() == "Y"

    @classmethod
    def setting_get_su_user(cls):
        """
        Username for running 'su -' so scans are not run as root
        """
        try:
            return cls.objects.get(key="SU_USER").value
        except ObjectDoesNotExist:
            return None

    @classmethod
    def setting_waiver_is_overdue(cls):
        """Number of days when run is marked as not processed -- default value"""
        return int(cls.objects.get(key="WAIVER_IS_OVERDUE").value)

    @classmethod
    def settings_get_analyzers_versions_cache_duration(cls):
        """ how long before next check (in hours)"""
        try:
            return int(get_or_none(cls, key="ANALYZERS_VERSIONS_CACHE_DURATION").value)
        except AttributeError:
            return None

    @classmethod
    def settings_set_last_versions_check(cls, mock_config):
        obj, _ = cls.objects.get_or_create(key="ANALYZERS_VERSIONS_LAST_CHECKED")
        try:
            value = json.loads(obj.value)
        except TypeError:
            value = {}
        value[mock_config] = datetime.datetime.now().isoformat()
        obj.value = json.dumps(value)
        obj.save()

    @classmethod
    def settings_get_last_versions_check(cls, mock_config=None):
        """
        Timestamp when last check was performed
        {'mock_config': 'iso_timestamp', ...}
        """
        versions = get_or_none(cls, key="ANALYZERS_VERSIONS_LAST_CHECKED")
        if versions:
            versions = json.loads(versions.value)
            if mock_config:
                return versions.get(mock_config, None)
            return versions

    @classmethod
    def settings_get_results_tb_exclude_dirs(cls):
        dirs = get_or_none(cls, key="RESULTS_TB_EXCLUDE_DIRS")
        if dirs:
            return json.loads(dirs.value)


class ClientAnalyzerMixin:
    def verify_by_name(self, name):
        try:
            model = self.get(cli_long_command=name)
        except ObjectDoesNotExist:
            logger.error("Analyzer %s doesn't exist", name)
            raise
        else:
            if not model.enabled:
                raise RuntimeError('Analyzer %s is disabled', model)
            return model

    def verify_in_bulk(self, analyzers):
        result = []
        for a in analyzers:
            result.append(self.verify_by_name(a).id)
        return self.filter(id__in=result)

    def list_available(self):
        return self.filter(enabled=True)

    def export_available(self):
        return list(self.list_available().values(
            'analyzer__name', 'version', 'cli_long_command'))

    def filter_by_long_arg(self, long_opts):
        return self.list_available().filter(cli_long_command__in=long_opts)

    def get_opts(self, analyzers):
        """
        get_opts([<ClientAnalyzer>, <...>, ...])
         -> {'analyzers': 'gcc,cppcheck,...', 'args': '-a -b']}
        """
        analyzer_list = list(analyzers.values_list('build_append', flat=True))
        args_list = list(analyzers.values_list('build_append_args', flat=True))
        response = {
            'analyzers': analyzer_list,
            'args': args_list,
        }
        return response

    def is_valid(self, analyzer):
        return self.list_available().filter(cli_long_command=analyzer).exists()


class ClientAnalyzerQuerySet(models.query.QuerySet, ClientAnalyzerMixin):
    pass


class ClientAnalyzerManager(models.Manager, ClientAnalyzerMixin):
    def get_queryset(self):
        return ClientAnalyzerQuerySet(self.model, using=self._db)


class ClientAnalyzer(models.Model):
    analyzer = models.ForeignKey("Analyzer", blank=True, null=True, on_delete=models.CASCADE)
    version = models.CharField(max_length=32, blank=True, null=True)
    enabled = models.BooleanField(default=True)
    # what osh-cli option enables analyzer
    cli_long_command = models.CharField(max_length=32, blank=False, null=False)
    # enable this analyzer with csmock -t <build_append>[,<build_append>...]
    build_append = models.CharField(max_length=32, blank=True, null=True,
                                    help_text="analyzer name to put in --tools")
    # args to append, e.g. --use-host-cppcheck
    build_append_args = models.CharField(max_length=256, blank=True, null=True)

    objects = ClientAnalyzerManager()

    class Meta:
        ordering = ['analyzer', 'version']

    def __str__(self):
        return "%s %s" % (self.analyzer, self.version)

    @classmethod
    def chain_to_list(cls, chain):
        return re.split(r'[;,:]', chain.strip())


class Analyzer(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return "%s" % (self.name)


class AnalyzerVersionManager(models.Manager):
    def get_or_create_(self, analyzer_name, version):
        analyzer, _ = Analyzer.objects.get_or_create(name=analyzer_name)
        version_model, _ = self.get_or_create(version=version, analyzer=analyzer)
        return version_model

    def get_or_create_bulk(self, analyzers, mock):
        for analyzer in analyzers:
            v = self.get_or_create_(analyzer['name'], analyzer['version'])
            v.mocks.add(mock)

    def update_analyzers_versions(self, analyzers, mock_name):
        """ update mock profile with latest analyzer versions """
        # has to be in one transaction because we clear all analyzers first
        # and then populate the set with actual analyzers
        with transaction.atomic():
            mock = MockConfig.objects.get(name=mock_name)
            mock.analyzers.clear()
            self.get_or_create_bulk(analyzers, mock)
            AppSettings.settings_set_last_versions_check(mock_name)

    def is_cache_uptodate(self, mock_name):
        """ according to configuration, are versions up to date, or should we check? """
        duration = AppSettings.settings_get_analyzers_versions_cache_duration()
        if duration is None:
            raise RuntimeError('Configure ANALYZERS_VERSIONS_CACHE_DURATION in AppSettings.')
        now = datetime.datetime.now()
        last_checked_iso = AppSettings.settings_get_last_versions_check(mock_name)
        if last_checked_iso is None:
            return False
        last_checked = datetime.datetime.strptime(last_checked_iso, "%Y-%m-%dT%H:%M:%S.%f")
        delta = datetime.timedelta(hours=duration)
        return last_checked + delta > now

    def get_analyzer_versions_for_mockprofile(self, mock_name):
        """
        return serializable data wrt analyzers for given mock profile
        {'gcc': '123', 'clang': '456', ...}
        """
        return self.filter(mocks__name=mock_name)


class AnalyzerVersion(models.Model):
    version = models.CharField(max_length=64)
    analyzer = models.ForeignKey(Analyzer, on_delete=models.CASCADE)
    mocks = models.ManyToManyField(MockConfig, blank=True, related_name="analyzers")
    date_created = models.DateTimeField(auto_now_add=True)

    objects = AnalyzerVersionManager()

    class Meta:
        get_latest_by = 'date_created'

    def __str__(self):
        return "%s-%s" % (self.analyzer, self.version)


class ProfileManager(models.Manager):
    def get_analyzers_and_args_for_profile(self, profile_name):
        """return list of string of analyzers' names and string with additional args"""
        try:
            profile = self.get(name=profile_name)
        except ObjectDoesNotExist:
            logger.error("profile %s does not exist", profile_name)
            raise ObjectDoesNotExist("profile %s does not exist" % profile_name)
        else:
            analyzer_list = ClientAnalyzer.chain_to_list(profile.analyzers)
            args_list = profile.csmock_args
            return analyzer_list, args_list

    def export_available(self):
        return self.filter(enabled=True).values("name", "description")


# TODO: We should replace this key with a One-to-Many releation with Analyzer.
def _validate_command_arguments(cmd_args):
    if 'analyzers' not in cmd_args:
        raise ValidationError('Command arguments must contain the "analyzers" key.')

    analyzers = cmd_args['analyzers']
    if not analyzers:
        raise ValidationError('Command arguments contain an empty "analyzers" key.')

    errors = [
        ValidationError(f'Command arguments contain unknown analyzer: "{analyzer}"')
        for analyzer in analyzers.split(',')
        if not Analyzer.objects.filter(name=analyzer)
    ]

    if errors:
        raise ValidationError(errors)


class Profile(models.Model):
    """
    Preconfigured setups, e.g.: python, c, aggresive c, ...
    """
    name = models.CharField(max_length=64)
    description = models.TextField(null=True, blank=True)
    enabled = models.BooleanField(default=True)
    command_arguments = models.JSONField(
        default=dict,
        help_text="this field has to contain key 'analyzers', "
                  "which is a comma separated list of analyzers, "
                  "optionally add key csmock_args, which is a string",
        validators=[_validate_command_arguments])

    objects = ProfileManager()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return "%s: %s" % (self.name, self.command_arguments)

    @property
    def analyzers(self):
        return self.command_arguments['analyzers']

    @property
    def csmock_args(self):
        try:
            return self.command_arguments['csmock_args']
        except KeyError:
            # there are no arguments, this is not an error
            logger.info("No csmock arguments for profile '%s'", self)
            return ''
