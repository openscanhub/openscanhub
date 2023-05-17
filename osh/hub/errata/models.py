# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import logging

from django.db import models

from osh.hub.scan.models import Profile

logger = logging.getLogger(__name__)


class ScanningSessionBindingMixin:

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

    options = models.JSONField(default=dict, blank=True)

    profile = models.ForeignKey(Profile, blank=True, null=True, on_delete=models.CASCADE)

    objects = ScanningSessionBindingManager()

    def __str__(self):
        return "[%s %s]" % (self.name, self.options)

    def get_option(self, name):
        try:
            return self.options[name]
        except KeyError:
            logger.error("No option '%s' in %s", name, self)
            return
