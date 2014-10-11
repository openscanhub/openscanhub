# -*- coding: utf-8 -*-
from glob import glob
import json
import re
import os
import datetime
import logging
import cPickle as pickle
from covscanhub.other import get_or_none

from covscanhub.scan.messaging import post_qpid_message
from covscanhub.other.scan import remove_duplicities

from django.db import models, transaction
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from kobo.hub.models import Task
from kobo.types import Enum, EnumItem
from kobo.client.constants import TASK_STATES
from kobo.django.fields import JSONField

logger = logging.getLogger(__name__)

#south does not know JSONField
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^kobo\.django\.fields\.JSONField"])


SCAN_STATES = Enum(
    "QUEUED",            # scan was submitted, waiting for scheduler
    "SCANNING",          # scan/task is active now
    "NEEDS_INSPECTION",  # scan finished and there are defects which need
                         #  owner's attention
    "WAIVED",            # user appropriately waived each defect
    "PASSED",            # scan didn't discover new defects; everything is fine
    "FINISHED",          # scan finished -- USER/ERRATA_BASE scans only
    "FAILED",            # scan has failed, need an attention by covscan admins
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


class MockConfigMixin(object):
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
    def get_query_set(self):
        return MockConfigQuerySet(self.model, using=self._db)


class MockConfig(models.Model):
    name = models.CharField(max_length=256, unique=True)
    enabled = models.BooleanField(default=True)

    objects = MockConfigManager()

    class Meta:
        ordering = ("name", )

    def __unicode__(self):
        return self.name

    def export(self):
        result = {
            "name": self.name,
            "enabled": self.enabled,
        }
        return result


class SystemReleaseMixin(object):
    def active(self):
        return self.filter(active=True)


class SystemReleaseQuerySet(models.query.QuerySet, SystemReleaseMixin):
    pass


class SystemReleaseManager(models.Manager, SystemReleaseMixin):
    def get_query_set(self):
        return SystemReleaseQuerySet(self.model, using=self._db)


class SystemRelease(models.Model):
    """
    Represents release for which are scans submitted
    """
    # rhel-6.4 | rhel-7 etc.
    tag = models.CharField("Short tag", max_length=16, blank=False)

    #Red Hat Enterprise Linux 6 etc.
    product = models.CharField("Product name", max_length=128, blank=False)

    # release number (y) -- RHEL-x.y
    release = models.IntegerField()

    active = models.BooleanField(default=True, help_text="If set to True,\
statistical data will be harvested for this system release.")

    parent = models.OneToOneField("self", blank=True, null=True)

    objects = SystemReleaseManager()

    def __unicode__(self):
        return u"%s -- %s.%d" % (self.tag, self.product, self.release)

    def get_child(self):
        try:
            return self.systemrelease
        except ObjectDoesNotExist:
            return None

    child = property(get_child)

    def get_prod_ver(self):
        """
        return product version (such as 7.0, 6.4, etc.), created for BZ
        """
        return "%s.%s" % (re.search('(\d)', self.product).group(1),
                          self.release)


class TagMixin(object):
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
    def get_query_set(self):
        return TagQuerySet(self.model, using=self._db)


class Tag(models.Model):
    """
    Mapping between brew tags and mock configs
    """

    name = models.CharField("Brew Tag", max_length=64, blank=False)
    mock = models.ForeignKey(MockConfig, verbose_name="Mock Config",
                             blank=False, null=False,
                             related_name='mock_profile')
    release = models.ForeignKey(SystemRelease, related_name='system_release')

    objects = TagManager()

    def __unicode__(self):
        return "Tag: %s --> Mock: %s (%s)" % \
            (self.name, self.mock, self.release)


class PackageMixin(object):
    def get_or_create_by_name(self, name):
        model, created = self.get_or_create(name=name)
        return model


class PackageQuerySet(models.query.QuerySet, PackageMixin):
    pass


class PackageManager(models.Manager, PackageMixin):
    def get_query_set(self):
        return PackageQuerySet(self.model, using=self._db)


class Package(models.Model):
    """
    model that represents packages, these are linked directly to scans
    """
    name = models.CharField("Package name", max_length=64,
                            blank=False, null=False)
    blocked = models.NullBooleanField(default=False, help_text="If this is set to \
True, the package is blacklisted -- not accepted for scanning.", blank=True, null=True)
    eligible = models.NullBooleanField(default=True,
                                       help_text="DEPRECATED, do not use; use package attribute instead.",
                                       blank=True, null=True)

    objects = PackageManager()

    def __unicode__(self):
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
        if sb.result is not None:
            response += u'<div style="margin-left: %dem">%s<a \
href="%s">%s</a> (%s) New defects: %d, fixed defects: %d</div>\n' % (
                indent_level if indent_level <= 1 else indent_level * 2,
                u'\u2570\u2500\u2500' if indent_level > 0 else u'',
                reverse("waiving/result", args=(sb.result.id,)),  # url
                sb.scan.nvr,
                sb.scan.get_state_display(),
                sb.result.new_defects_count(),
                sb.result.fixed_defects_count(),
            )
        else:
            response += u"%s%s<br/ >\n" % (
                u"&nbsp;" * indent_level * 4,
                sb.scan.nvr,
            )
        if indent_level == 0:  # BASE
            if response.endswith('</div>\n'):
                response = response[:-7]
            response += u'<span style="position:absolute; left: 45em">\
Base: %s</span></div>\n' % (sb.scan.base.nvr)
        return self.display_graph(scan.parent,
                                  response, indent_level + 1)

    def display_scan_tree(self):
        scans = Scan.objects.filter(package=self)
        if not scans:
            return mark_safe('There are no scans submitted related to this \
package')
        releases = scans.values('tag__release').distinct()
        response = ""

        for release in releases:
            scans_package = scans.filter(
                tag__release__id=release['tag__release'],
                scan_type__in=SCAN_TYPES_TARGET)
            if not scans_package:
                response += u"No scans in this release.<hr/ >\n"
                continue
            first_scan = scans_package.order_by('date_submitted')[0]
            response += u"<div>\n<h3>%s release %d</h3>\n" % (
                first_scan.tag.release.product,
                first_scan.tag.release.release
            )
            response = self.display_graph(first_scan, response)
            response += u"<hr/ ></div>\n"
        return mark_safe(response)

    def is_blocked(self, release):
        try:
            atr = PackageAttribute.blocked(self, release)
        except ObjectDoesNotExist:
            return self.blocked
        else:
            return atr.is_blocked()

    def is_eligible(self, release):
        try:
            atr = PackageAttribute.eligible(self, release)
        except ObjectDoesNotExist:
            return self.eligible
        else:
            return atr.is_eligible()


class PackageAttributeMixin(object):
    def by_package(self, package):
        return self.filter(package=package)

    def by_release(self, release):
        return self.filter(release=release)

    def eligible(self):
        return self.filter(key=PackageAttribute.ELIGIBLE)

    def eligible_package_in_release(self, package, release):
        return self.get(package=package, release=release, key=PackageAttribute.ELIGIBLE)


class PackageAttributeQuerySet(models.query.QuerySet, PackageAttributeMixin):
    pass


class PackageAttributeManager(models.Manager, PackageAttributeMixin):
    def get_query_set(self):
        return PackageAttributeQuerySet(self.model, using=self._db)


class PackageAttribute(models.Model):
    """
    keys:
    BLOCKED: {Y | N}
     * If this is set to True, the package is blacklisted -- not accepted
    for scanning.
    
    ELIGIBLE: {Y | N}
     * Is package scannable? You may have package written in different language
    that is supported by your scanner.

    TODO: eligible should be more flexible:
        it should be M2M relation with table capability (C, Java, Python)
        capability should be linked with table Analyzers
    """
    BLOCKED = 'BLOCKED'
    ELIGIBLE = 'ELIGIBLE'

    key = models.CharField(max_length=64, null=True, blank=True)
    value = models.CharField(max_length=128, null=True, blank=True)
    package = models.ForeignKey(Package)
    release = models.ForeignKey(SystemRelease)

    objects = PackageAttributeManager()

    def __unicode__(self):
        return u"%s = %s (%s %s)" % (self.key, self.value, self.package, self.release)

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

    @classmethod
    def eligible(cls, package, release):
        try:
            return cls._get_for_package_in_release(package, release, PackageAttribute.ELIGIBLE)
        except ObjectDoesNotExist:
            logger.error("Package eligibility attribute not found: %s %s", package, release)
            raise

    def _is(self, key, exc_type):
        if self.key == key:
            return self.value == 'Y'
        else:
            raise ValueError('This attribute (%s) is not related to %s stuff.'
                             % (self.key, exc_type))

    def is_blocked(self):
        return self._is(PackageAttribute.BLOCKED, 'blocked')

    def is_eligible(self):
        return self._is(PackageAttribute.ELIGIBLE, 'eligible')

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

    @classmethod
    def create_eligible(cls, package, release, eligible):
        try:
            atr = cls.objects.eligible_package_in_release(package, release)
        except ObjectDoesNotExist:
            return cls.create_new_bool(package, release, PackageAttribute.ELIGIBLE, eligible)
        else:
            atr.value = eligible
            atr.save()
            return atr


class PackageCapabilityMixin(object):
    def get_or_create_(self, package, is_capable, release=None):
        model, created = self.get_or_create(package=package, is_capable=is_capable,
                                            release=release)
        return model


class PackageCapabilityQuerySet(models.query.QuerySet, PackageCapabilityMixin):
    pass


class PackageCapabilityManager(models.Manager, PackageCapabilityMixin):
    def get_query_set(self):
        return PackageCapabilityQuerySet(self.model, using=self._db)


class PackageCapability(models.Model):
    release = models.ForeignKey(SystemRelease, blank=True, null=True)
    package = models.ForeignKey(Package)
    is_capable = models.BooleanField()

    objects = PackageCapabilityManager()

    def __unicode__(self):
        return u"%s: %s" % (self.package, self.capability_set.all())


class ScanMixin(object):
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
    def get_query_set(self):
        return ScanQuerySet(self.model, using=self._db)


class ScanTargetMixin(object):
    pass


class ScanTargetQuerySet(models.query.QuerySet, ScanTargetMixin):
    pass


class ScanTargetManager(models.Manager, ScanTargetMixin):
    def get_query_set(self):
        return ScanTargetQuerySet(self.model, using=self._db).filter(scan_type__in=SCAN_TYPES_TARGET)


class Scan(models.Model):
    """
    Stores information about submitted scans from Errata Tool
    """
    #yum-3.4.3-42.el7
    nvr = models.CharField("NVR", max_length=512,
                           blank=False, help_text="Name-Version-Release")

    scan_type = models.PositiveIntegerField(default=SCAN_TYPES["ERRATA"],
                                            choices=SCAN_TYPES.get_mapping(),
                                            help_text="Scan Type")

    state = models.PositiveIntegerField(default=SCAN_STATES["INIT"],
                                        choices=SCAN_STATES.get_mapping(),
                                        help_text="Current scan state")

    #information for differential scan -- which version of package we are
    #diffing to
    base = models.ForeignKey('self', verbose_name="Base Scan",
                             blank=True, null=True,
                             help_text="NVR of package to diff against",
                             related_name="base_scan")
    #user scans dont have to specify this option -- allow None
    tag = models.ForeignKey(Tag, verbose_name="Tag",
                            blank=True, null=True,
                            help_text="Tag from brew")

    username = models.ForeignKey(settings.AUTH_USER_MODEL)

    #date when there was last access to scan
    #should change when:
    #   - scan has finished
    #   - waiver added
    #   - waiver invalidated
    last_access = models.DateTimeField(blank=True, null=True)

    date_submitted = models.DateTimeField(auto_now_add=True)

    enabled = models.BooleanField(default=True, help_text="This scan is \
counted in statistics.")

    package = models.ForeignKey(Package)

    parent = models.ForeignKey('self', verbose_name="Parent Scan", blank=True,
                               null=True, related_name="parent_scan")

    objects = ScanManager()
    targets = ScanTargetManager()

    class Meta:
        get_latest_by = "date_submitted"

    def __unicode__(self):
        prefix = u"#%s %s %s" % (self.id,
                                 self.nvr,
                                 self.get_state_display())
        if self.base:
            return u"%s Base: %s" % (prefix, self.base.nvr)
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
            return u"red_font"
        else:
            return u""

    def waived_on_time(self):
        """
        either scan is processed (passed/waived) or user still has time to
        process it; use release specific setting if exist, fallback to default

        Return:
            - None -- scan does not need to be waived
            - True -- processed on time/still has time to process it
            - False -- do not processed on time
        """
        if self.state not in SCAN_STATES_FINISHED_BAD:
            try:
                d = AppSettings.settings_waiver_overdue_by_release(
                    self.tag.release.tag)
            except KeyError:
                d = AppSettings.setting_waiver_is_overdue()
            except Exception, e:
                logger.error('Failed to get release specific waiver overdue \
setting: %s', e)
            return self.state in SCAN_STATES_PROCESSED or \
                self.last_access > datetime.datetime.now() + d
        else:
            return None


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


class ScanBindingMixin(object):
    def latest_packages_scans(self):
        ids = []
        q = self.finished_well()
        for p_id in q.values_list('scan__package', flat=True).distinct():
            p = q.filter(scan__package__id=p_id)
            for base in p.values_list('scan__base__nvr', flat=True).distinct():
                ids.append(p.filter(scan__base__nvr=base).latest().id)
        return self.filter(id__in=ids)

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
    def get_query_set(self):
        return ScanBindingQuerySet(self.model, using=self._db)


class TargetScanBindingManager(models.Manager, ScanBindingMixin):
    def get_query_set(self):
        return ScanBindingQuerySet(self.model, using=self._db).filter(scan__scan_type__in=SCAN_TYPES_TARGET)


class ScanBinding(models.Model):
    """
    Binding between scan, task and result -- for easier creation of scans that
    are already submitted
    """
    task = models.OneToOneField(Task, verbose_name="Asociated Task",
                                help_text="Asociated task on worker",
                                blank=True, null=True,)
    scan = models.OneToOneField(Scan,
                                verbose_name="Scan")
    result = models.OneToOneField("waiving.Result",
                                  blank=True, null=True,)

    objects = ScanBindingManager()

    targets = TargetScanBindingManager()

    class Meta:
        get_latest_by = "result__date_submitted"

    def __unicode__(self):
        return u"#%d: Scan: %s | %s" % (self.id, self.scan, self.task)

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
        if len(analyzers) != len(sb_analyzers):
            logger.info("Analyzer sets don't match: %s != %s", analyzers, sb_analyzers)
            return False
        for a in analyzers:
            for sb_a in sb_analyzers:
                if a.analyzer.name == sb_a.analyzer.name:
                    if not a.version == sb_a.version:
                        logger.info("%s-%s != %s-%s", a.analyzer.name, a.version,
                                    sb_a.analyzer.name, sb_a.version)
                        # one of the version doesn't match
                        return False
                    else:
                        # continue with another analyzer
                        break
        return True

    def is_actual(self):
        """ is scan actual? ~ scanned with up to date analyzers """
        try:
            mock_profile = self.scan.tag.mock.name
        except AttributeError:
            return False
        else:
            analyzers = AnalyzerVersion.objects.get_analyzer_versions_for_mockprofile(mock_profile)
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

    def __unicode__(self):
        return u"#%d (%d) %s %s" % (self.id, self.priority,
                                    self.release_tag, self.template)

    def get_tag(self, rhel_version):
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
    # self.id is covscan_internal_target_run_id (formerly scanbinding.id)
    latest_run = models.ForeignKey(ScanBinding, null=True, blank=True)
    comment = models.CharField(max_length=256, default="", blank=True)
    state = models.PositiveIntegerField(
        default=REQUEST_STATES['OK'],
        choices=REQUEST_STATES.get_mapping(),
        help_text="Status of request"
    )

    def __unicode__(self):
        return u"#%d Advisory: %s %s" % (self.id, self.advisory_id,
                                         self.latest_run)

    def set_latest_run(self, sb, save=True):
        self.latest_run = sb
        if save:
            self.save()


class AppSettings(models.Model):
    """
    Settings for covscan stored in DB so they can be easily changed.

    SEND_EMAIL { Y, N }
    SEND_BUS_MESSAGE { Y, N }

    CHECK_USER_CAN_SUBMIT_SCAN { Y, N }

    WAIVER_IS_OVERDUE pickled/jsoned datetime.delta
    WAIVER_IS_OVERDUE_RELSPEC release specific ^

    ACTUAL_SCANNER tuple('coverity', '6.5.0')

    DEFAULT_SCANNING_COMMAND -- command for running analysis
     * this string should accept these dynamic variables:
      * srpm_path -- absolute path to SRPM
      * tmp_dir -- temporary created dir
      * mock_profile -- mock profile used for analysis
    SCANNING_COMMAND_RELSPEC -- override of default
    """
    key = models.CharField(max_length=128, blank=False, null=False)
    value = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "AppSettings"

    def __unicode__(self):
        return u"%s = %s" % (self.key, self.value)

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
        """Time period when run is marked as not processed -- default value"""
        try:
            return pickle.loads(
                str(cls.objects.get(key="WAIVER_IS_OVERDUE").value))
        except Exception:
            return json.loads(
                str(cls.objects.get(key="WAIVER_IS_OVERDUE").value))

    @classmethod
    def settings_waiver_is_overdue_relspec(cls):
        """
        Release specific overdue values
        The are stored in DB like this:
            pickle.dumps('release__tag', 'timedelta')
        """
        q = cls.objects.filter(key="WAIVER_IS_OVERDUE_RELSPEC")
        try:
            return dict(pickle.loads(str(o.value)) for o in q)
        except Exception:
            return dict(json.loads(str(o.value)) for o in q)

    @classmethod
    def settings_waiver_overdue_by_release(cls, short_tag):
        """
        Return release specific overdue value for provided release shorttag
        """
        return cls.settings_waiver_is_overdue_relspec()[short_tag]

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


class TaskExtension(models.Model):
    task = models.OneToOneField(Task)
    secret_args = JSONField(default={})

    def __unicode__(self):
        return u"%s %s" % (self.task, self.secret_args)


class ClientAnalyzerMixin(object):
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
            'analyzer__name', 'version', 'cli_short_command', 'cli_long_command'))

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
    def get_query_set(self):
        return ClientAnalyzerQuerySet(self.model, using=self._db)


class ClientAnalyzer(models.Model):
    analyzer = models.ForeignKey("Analyzer", blank=True, null=True)
    #name = models.CharField(max_length=64)
    version = models.CharField(max_length=32, blank=True, null=True)
    enabled = models.BooleanField(default=True)
    # what covscan-client option enables analyzer
    cli_short_command = models.CharField(max_length=32, blank=True, null=True)
    cli_long_command = models.CharField(max_length=32, blank=False, null=False)
    # enable this analyzer with csmock -t <build_append>[,<build_append>...]
    build_append = models.CharField(max_length=32, blank=True, null=True,
                                    help_text="analyzer name to put in --tools")
    # args to append, e.g. --use-host-cppcheck
    build_append_args = models.CharField(max_length=256, blank=True, null=True)

    objects = ClientAnalyzerManager()

    def __unicode__(self):
        return u"%s %s" % (self.analyzer, self.version)

    @classmethod
    def chain_to_list(cls, chain):
        return re.split(r'[;,:]', chain.strip())


class Analyzer(models.Model):
    name = models.CharField(max_length=64)

    def __unicode__(self):
        return u"%s" % (self.name)


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
    analyzer = models.ForeignKey(Analyzer)
    mocks = models.ManyToManyField(MockConfig, blank=True, null=True, related_name="analyzers")
    date_created = models.DateTimeField(auto_now_add=True)

    objects = AnalyzerVersionManager()

    class Meta:
        get_latest_by = 'date_created'

    def __unicode__(self):
        return u"%s-%s" % (self.analyzer, self.version)


class ProfileManager(models.Manager):
    def get_analyzers_and_args_for_profile(self, profile_name):
        """return list of string of analyzers' names and string with additional args"""
        try:
            profile = self.get(name=profile_name)
        except ObjectDoesNotExist:
            logger.error("profile %s does not exist", profile_name)
            raise ObjectDoesNotExist("profile %s does not exist" % profile_name)
        else:
            analyzer_list = ClientAnalyzer.chain_to_list(profile.command_arguments.get('analyzers', ''))
            args_list = profile.command_arguments.get('csmock_args', '')
            return analyzer_list, args_list

    def export_available(self):
        return self.filter(enabled=True).values("name", "description")


class Profile(models.Model):
    """
    Preconfigured setups, e.g.: python, c, aggresive c, ...
    """
    name = models.CharField(max_length=64)
    description = models.TextField(null=True, blank=True)
    enabled = models.BooleanField(default=True)
    command_arguments = JSONField(
        default={},
        help_text="this field has to contain key 'analyzers', "
                  "which is a comma separated list of analyzers, "
                  "optionally add key csmock_args, which is a string")

    objects = ProfileManager()

    def __unicode__(self):
        return u"%s: %s" % (self.name, self.command_arguments)

    @property
    def analyzers(self):
        try:
            return self.command_arguments['analyzers']
        except KeyError:
            logger.error('profile doesn\'t have any analyzers: %s', self.command_arguments)
            raise RuntimeError('no analyzers in profile %s', self)
