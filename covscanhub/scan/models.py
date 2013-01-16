# -*- coding: utf-8 -*-


import re
import datetime

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from kobo.hub.models import Task
from kobo.types import Enum
from kobo.client.constants import TASK_STATES


#south does not know JSONField
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^kobo\.django\.fields\.JSONField"])


SCAN_STATES = Enum(
    "QUEUED",            # scan was submitted, waiting for scheduler
    "SCANNING",          # scan/task is active now
    "NEEDS_INSPECTION",  # scan finished and there are some unwaived things
    "WAIVED",            # scan finished and everything is okay -- waived
    "PASSED",            # nothing new
    "FINISHED",          # scan finished -- USER/ERRATA_BASE scans only
    "FAILED",            # scan failed -- this shouldn't happened
    "BASE_SCANNING",     # child scan is in scanning process right now
    "CANCELED",          # there is new build of package, this one is obsolete
)

SCAN_TYPES = Enum(
    "ERRATA",           # this scan was submitted from ET
    # base scan for ERRATA does not exist (this is basicly just mock build)
    "ERRATA_BASE",
    "USER",             # some user posted this scan
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


class MockConfig(models.Model):
    name = models.CharField(max_length=256, unique=True)
    enabled = models.BooleanField(default=True)

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


class SystemRelease(models.Model):
    """
    Represents release for which are scans submitted
    """
    # rhel-6.4 | rhel-7 etc.
    tag = models.CharField("Short tag", max_length=16, blank=False)

    #Red Hat Enterprise Linux 6 etc.
    product = models.CharField("Product name", max_length=128, blank=False)

    # release number (y)
    release = models.IntegerField()

    active = models.BooleanField(default=True, help_text="If set to True,\
statistical data will be harvested for this system release.")

    parent = models.OneToOneField("self", blank=True, null=True)

    def get_child(self):
        try:
            return self.systemrelease
        except ObjectDoesNotExist:
            return None

    child = property(get_child)

    def __unicode__(self):
        return u"%s -- %s.%d" % \
            (self.tag, self.product, self.release)

    def get_prod_ver(self):
        """
        return product version (such as 7.0, 6.4, etc.), created for BZ
        """
        return "%s.%s" % (re.search('(\d)', self.product).group(1),
                          self.release)


class Tag(models.Model):
    """
    Mapping between brew tags and mock configs
    """

    name = models.CharField("Brew Tag", max_length=64, blank=False)
    mock = models.ForeignKey(MockConfig, verbose_name="Mock Config",
                             blank=False, null=False,
                             related_name='mock_profile')
    release = models.ForeignKey(SystemRelease, related_name='system_release')

    def __unicode__(self):
        return "Tag: %s --> Mock: %s (%s)" % \
            (self.name, self.mock, self.release)


class Package(models.Model):
    """
    Package name -- for statistics purposes mainly
    """
    name = models.CharField("Package name", max_length=64,
                            blank=False, null=False)
    blocked = models.BooleanField(default=False, help_text="If this is set to \
True, this package will be blacklisted -- not accepted for scanning.")

    def __unicode__(self):
        return "#%s %s" % \
            (self.id, self.name)

    def calculateScanNumbers(self):
        return Scan.objects.filter(package=self,
                                   scan_type=SCAN_TYPES['ERRATA']).count()

    scans_number = property(calculateScanNumbers)

    def get_latest_scans(self):
        srs = SystemRelease.objects.filter(active=True)
        response = ""
        for sr in srs:
            try:
                scan = Scan.objects.get(package=self, tag__release=sr,
                                        enabled=True)
            except ObjectDoesNotExist:
                pass
            else:
                response += '%s: <a href="%s">%s</a>' % (
                    sr.tag,
                    reverse("waiving/result/newest", args=(self.name, sr.tag)),
                    scan.nvr,
                )
        if response == "":
            return "None"
        return mark_safe(response)

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
                scan_type=SCAN_TYPES['ERRATA'])
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
    state = models.PositiveIntegerField(default=SCAN_STATES["QUEUED"],
                                        choices=SCAN_STATES.get_mapping(),
                                        help_text="Current scan state")
    username = models.ForeignKey(User)

    #date when there was last access to scan
    #should change when:
    #   - scan has finished
    #   - user opens waiving page
    #   - anytime user changes something (waive something, etc.)
    last_access = models.DateTimeField(blank=True, null=True)

    date_submitted = models.DateTimeField(auto_now_add=True)

    enabled = models.BooleanField(default=True, help_text="This scan is \
counted in statistics.")

    package = models.ForeignKey(Package)

    parent = models.ForeignKey('self', verbose_name="Parent Scan", blank=True,
                               null=True, related_name="parent_scan")

    def __unicode__(self):
        if self.base is None:
            return u"#%s [%s]" % (self.id, self.nvr)
        else:
            return u"#%s [%s, Base: %s]" % (self.id, self.nvr, self.base.nvr)

    def is_errata_scan(self):
        return self.scan_type == SCAN_TYPES['ERRATA']

    def is_errata_base_scan(self):
        return self.scan_type == SCAN_TYPES['ERRATA_BASE']

    def is_user_scan(self):
        return self.scan_type == SCAN_TYPES['USER']

    @classmethod
    def create_scan(cls, scan_type, nvr, tag, username, package,
                    enabled, base=None):
        scan = cls()
        scan.scan_type = scan_type
        scan.nvr = nvr
        scan.base = base
        scan.tag = tag
        scan.state = SCAN_STATES["QUEUED"]
        scan.username = User.objects.get_or_create(username=username)[0]
        scan.last_access = datetime.datetime.now()
        scan.package = package
        scan.enabled = enabled
        scan.save()
        return scan

    def get_errata_id(self):
        if self.is_errata_scan():
            try:
                return self.scanbinding.task.args['errata_id']
            except KeyError:
                return None
        return None

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
            scan__scan_type=SCAN_TYPES['ERRATA']).\
            order_by('result__date_submitted')
        if related_scans:
            return related_scans[0]
        else:
            return None


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

    class Meta:
        get_latest_by = "result__date_submitted"

    def __unicode__(self):
        return u"#%d: Scan: %s | %s" % (self.id, self.scan, self.task)