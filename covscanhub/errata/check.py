# -*- coding: utf-8 -*-
"""
Functions related to checking provided data
"""

import logging

from covscanhub.errata.utils import depend_on
from covscanhub.other.exceptions import PackageBlacklistedException, PackageNotEligibleException
from covscanhub.scan.models import PackageAttribute, ScanBinding
from covscanhub.scan.xmlrpc_helper import cancel_scan

import koji
from kobo.rpmlib import parse_nvr
from django.conf import settings


logger = logging.getLogger(__name__)


def check_nvr(nvr):
    try:
        return parse_nvr(nvr)
    except ValueError:
        logger.error('%s is not a correct N-V-R', nvr)
        raise RuntimeError('%s is not a correct N-V-R' % nvr)


def check_package_eligibility(package, nvr, mock_profile, release, created):
    """
    check if package is eligible for scanning
    * has code in appropriate programming language
    * is not blacklisted
    """
    if created:
        logger.info('Package %s for %s was created', package, release)
        depends_on = depend_on(nvr, 'libc.so', mock_profile)
        atr = PackageAttribute.create_eligible(package, release, depends_on)
        is_eligible = atr.is_eligible()
    else:
        is_blocked = package.is_blocked(release)
        if is_blocked:
            raise PackageBlacklistedException('Package %s is blacklisted.' %
                                              (package.name))
        is_eligible = package.is_eligible(release)
    if not is_eligible:
        raise PackageNotEligibleException(
            'Package %s is not eligible for scanning.' % (package.name))


def check_package_is_blocked(package, release):
    is_blocked = package.is_blocked(release)
    if is_blocked:
        raise PackageBlacklistedException('Package %s is blacklisted.' %
                                          (package.name))


def check_obsolete_scan(package, release):
    bindings = ScanBinding.targets.by_package(package).by_release(release)
    for binding in bindings:
        if binding.scan.is_in_progress():
            cancel_scan(binding)


def check_build(nvr):
    brew_proxy = koji.ClientSession(settings.BREW_HUB)
    build = brew_proxy.getBuild(nvr)
    if build is None:
        raise RuntimeError("Brew build '%s' does not exist" % nvr)
    return nvr
