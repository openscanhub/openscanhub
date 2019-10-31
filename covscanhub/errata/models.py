# -*- coding: utf-8 -*-

import logging
from django.core.exceptions import ObjectDoesNotExist
from covscanhub.other.exceptions import PackageNotEligibleException

from covscanhub.scan.models import PackageCapability, Analyzer, Profile

from kobo.django.fields import JSONField
from django.db import models


logger = logging.getLogger(__name__)


class Capability(models.Model):
    """
    what is analyser capable of scanning
    """
    name = models.CharField(max_length=64)

    # 'module.function' which performs the check
    function = models.CharField(max_length=128)

    options = JSONField(default={}, blank=True)

    caps = models.ManyToManyField(PackageCapability)
    analyzers = models.ManyToManyField(Analyzer)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.function)

    def check_capability(self, nvr, mock_profile, package, release):
        """ check if provided package is capable """
        module_name, func_name = self.function.rsplit(".", 1)
        try:
            module = __import__(module_name, fromlist=['rock', 'n', 'roll'])
        except ImportError:
            logger.error("Cannot import function '%s' for capability check '%s'", self.function, self.name)
            return False
        kwargs = dict(self.options)
        kwargs['nvr'] = nvr
        kwargs['mock_profile'] = mock_profile
        func = getattr(module, func_name)
        try:
            is_capable = func(**kwargs)
        except Exception as ex:
            logger.error("Exception thrown during capability checking: %s", repr(ex))
            return False
        else:
            pc = PackageCapability.objects.get_or_create_(package, is_capable, release)
            self.caps.add(pc)
        return is_capable

    def package_has_capability(self, package, release):
        return PackageCapability.objects.filter(package=package, release=release, capability=self).exists()

    def package_is_capable(self, package, release):
        try:
            return PackageCapability.objects.get(package=package, release=release, capability=self).is_capable
        except ObjectDoesNotExist:
            return False


class ScanningSessionBindingMixin(object):

    def get_by_name(self, name):
        return self.get(name=name)

    def get_analyzers(self, session_id):
        return self.get(id=session_id).profile.analyzers


class ScanningSessionBindingQuerySet(models.query.QuerySet, ScanningSessionBindingMixin):
    pass


class ScanningSessionBindingManager(models.Manager, ScanningSessionBindingMixin):
    def get_queryset(self):
        return ScanningSessionBindingQuerySet(self.model, using=self._db)


class ScanningSession(models.Model):
    """
    This represents an instance of automatic scanning process
    """
    # this should be handled by computers
    name = models.CharField(max_length=64)
    # optional human-readable description
    description = models.CharField(max_length=128, blank=True, null=True)

    options = JSONField(default={}, blank=True)

    caps = models.ManyToManyField(Capability)

    profile = models.ForeignKey(Profile, blank=True, null=True, on_delete=models.CASCADE)

    objects = ScanningSessionBindingManager()

    def __unicode__(self):
        return u"[%s %s]" % (self.name, self.options)

    def get_option(self, name):
        try:
            return self.options[name]
        except KeyError:
            logger.error("No option '%s' in %s", name, self)
            return

    def check_capabilities(self, nvr, mock_profile, package, release):
        caps = self.caps.all()
        for cap in caps:
            if cap.package_has_capability(package, release):
                is_capable = cap.package_is_capable(package, release)
            else:
                is_capable = cap.check_capability(nvr, mock_profile, package, release)
            if not is_capable:
                raise PackageNotEligibleException(
                    'Package %s is not eligible for scanning.' % (package.name))

