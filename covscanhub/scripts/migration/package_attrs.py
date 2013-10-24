# -*- coding: utf-8 -*-

"""
Migration script for package attributes:
eligibility
blacklist
"""
from covscanhub.scan.models import Package, SystemRelease, PackageAttribute


active = SystemRelease.objects.active()

for release in active:
    for package in Package.objects.all():
        PackageAttribute.create_blocked(package, release, package.blocked)
        PackageAttribute.create_eligible(package, release, package.eligible)