# -*- coding: utf-8 -*-


import datetime
import re

from django.db import models
from kobo.hub.models import Task
from kobo.types import Enum
from django.contrib.auth.models import User


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
    name        = models.CharField(max_length=256, unique=True)
    enabled     = models.BooleanField(default=True)

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


class SystemRelease(models.Model)
    """
    
    """
    # rhel-6.4 | rhel-7 etc.
    tag = models.CharField("Short tag", max_length=16, blank=False)
    
    #Red Hat Enterprise Linux 6 release 4 etc.
    description = models.CharField("Description", max_length=128, blank=False)

class Tag(models.Model):
    """
    Mapping between brew tags and mock configs
    """

    name = models.CharField("Brew Tag", max_length=64, blank=False)
    mock = models.ForeignKey(MockConfig, verbose_name="Mock Config",
                             blank=False, null=False)
    release = models.ForeignKey(SystemRelease)
    def __unicode__(self):
        return "Tag: %s --> Mock: %s (%s)" % (self.name, str(self.mock))


class Package(models.Model):
    """
    Package name -- for statistics purposes mainly
    """
    name = models.CharField("Package name", max_length=64,
                            blank=False, null=False)
    blocked = models.BooleanField(default=False, help_text="If this is set to \
True, this package will be blacklisted -- not accepted for scanning.")


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
                             help_text="NVR of package to diff against")
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
    
    package = models.ForeignKey(Package)

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
    def create_scan(cls, scan_type, nvr, tag, task_id, username, base=None):
        # validation of nvr, creating appropriate package object
        pattern = '(.*)-(.*)-(.*)'
        m = re.match(pattern, nvr)
        if m is not None:
            package_name = m.group(1)
            package, created = Package.objects.get_or_create(name=package_name)

        else:
            raise RuntimeError('%s is not a correct N-V-R (does not match "%s"\
)' % (nvr, pattern))
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
        