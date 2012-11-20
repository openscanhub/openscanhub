# -*- coding: utf-8 -*-


import datetime

from covscanhub.waiving.models import Result

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from kobo.hub.models import Task
from kobo.types import Enum


SCAN_STATES = Enum(
    "QUEUED",            # scan was submitted, waiting for scheduler
    "SCANNING",          # scan/task is active now
    "NEEDS_INSPECTION",  # scan finished and there are some unwaived things
    "WAIVED",            # scan finished and everything is okay -- waived
    "PASSED",            # nothing new
    "FINISHED",          # scan finished -- USER/ERRATA_BASE scans only
    "FAILED",            # scan failed -- this shouldn't happened
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
             'Enables user to submit scans via XML-RPC for Errata Tool'),
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

    #Red Hat Enterprise Linux 6 release 4 etc.
    description = models.CharField("Description", max_length=128, blank=False)
    
    active = models.BooleanField(default=True, help_text="If set to True,\
statistical data will be harvested for this system release.")

    def __unicode__(self):
        return "%s -- %s" % \
            (self.tag, self.description)


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

    def display_graph(self, parent_scan, response, indent_level=1):
        scan = parent_scan.get_child_scan()
        if scan is not None:  # TARGET
            response += '%s<a href="%s">%s</a> New defects: %d, fixed \
defects: %d<br/ >' % (
                "&nbsp;" * indent_level * 4,
                reverse("waiving/result",
                        args=(Result.objects.get(scan=scan).id,)),
                scan.nvr,
                Result.objects.get(scan=scan).new_defects_count(),
                Result.objects.get(scan=scan).fixed_defects_count(),)
            return self.display_graph(scan, response, indent_level + 1)
        else:  # BASE
            if response.endswith('<br/ >'):
                response = response[:-6]
            response += '%sBase: %s<br/ >' % (
                '.' * (160 - (indent_level * 4 + len(parent_scan.base.nvr))),
                parent_scan.base.nvr
            )
            return response

    def display_scan_tree(self):
        scans = Scan.objects.filter(package=self)
        releases = scans.values('tag__release').distinct()
        response = ""

        for release in releases:
            parent_scan = scans.get(tag__release__id=release['tag__release'],
                                    parent=None,
                                    scan_type=SCAN_TYPES['ERRATA'])
            response += "<div>\n<h3>%s</h3>\n" % \
                parent_scan.tag.release.description
            response += '<a href="%s">%s</a><br/ >\n' % (
                reverse("waiving/result",
                        args=(Result.objects.get(scan=parent_scan).id,)),
                parent_scan.nvr
            )
            response = self.display_graph(parent_scan, response)
            response += "<hr/ ></div>\n"
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
    task = models.ForeignKey(Task, verbose_name="Asociated Task",
                             help_text="Asociated task on worker")
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
    def create_scan(cls, scan_type, nvr, tag, task_id, username, package,
                    base=None):
        scan = cls()
        scan.scan_type = scan_type
        scan.nvr = nvr
        scan.base = base
        scan.tag = tag
        scan.task = Task.objects.get(id=task_id)
        scan.state = SCAN_STATES["QUEUED"]
        scan.username = User.objects.get(username=username)
        scan.last_access = datetime.datetime.now()
        scan.package = package
        scan.save()
        return scan

    def get_errata_id(self):
        if self.is_errata_scan():
            try:
                return self.task.args['errata_id']
            except KeyError:
                return None
        return None

    def get_child_scan(self):
        try:
            return Scan.objects.get(parent=self)
        except ObjectDoesNotExist:
            return None

    def get_latest_result(self):
        try:
            return Result.objects.filter(scan=self).latest()
        except ObjectDoesNotExist:
            return None