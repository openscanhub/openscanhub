# -*- coding: utf-8 -*-

"""
    Module that contains various statistics types. These functions are loaded
    dynamically. There is database record for each function.

    Functions get_*_by_release return dictionary with structure:
    {
        covscanhub.models.SystemRelease: value        
    }
"""

from covscanhub.scan.models import Scan, Package, SystemRelease, SCAN_TYPES
from covscanhub.waiving.models import Result

from django.db.models import Sum


#######
# SCANS
#######


def get_total_scans():
    """
        Number of all scans.
    """
    return Scan.objects.filter(scan_type=SCAN_TYPES['ERRATA']).count()


def get_scans_by_release():
    """
        Number of scans by release.
    """
    releases = SystemRelease.objects.all()
    result = {}
    for s in releases:
        result[s.id] = Scan.objects.filter(scan_type=SCAN_TYPES['ERRATA'],
                                           tag__release=s.id).count()
    return result

#####
# LOC
#####


def get_total_lines():
    """
        Number of LoC scanned.
    """
    return Result.objects.all().aggregate(Sum('lines'))['lines__sum']


def get_lines_by_release():
    """
        Number of LoC scanned by RHEL release.
    """
    releases = SystemRelease.objects.all()
    result = {}
    for s in releases:
        result[s.id] = Result.objects.filter(scan__tag__release=s.id)\
                        .aggregate(Sum('lines'))['lines__sum']
    return result

#########
# DEFECTS
#########


def get_total_fixed_defects():
    """
        Number of fixed defects found.
    """


def get_fixed_defects_by_release():
    """
        Number of fixed defects found by release.
    """


def get_total_new_defects():
    """
        Number of newly introduced defects.
    """


def get_new_defects_by_release():
    """
        Number of newly introduced defects by release.
    """


def get_fixed_defects_by_package():
    """
        Number of defects that were fixed between first scan and final one
    """

#########
# WAIVERS
#########


def get_total_waivers_submitted():
    """
        Number of waivers submitted.
    """


def get_waivers_submitted_by_release():
    """
        Number of waivers submitted by release.
    """


def get_total_missing_waivers():
    """
        Number of tests that were not waived.
    """


def get_total_missing_waivers_by_release():
    """
        Number of tests that were not waived by release.
    """


def get_total_is_a_bug_waivers():
    """
        Number of waivers with type IS_A_BUG.
    """


def get_is_a_bug_waivers_by_release():
    """
        Number of waivers with type IS_A_BUG by release.
    """


def get_total_not_a_bug_waivers():
    """
        Number of waivers with type NOT_A_BUG.
    """


def get_not_a_bug_waivers_by_release():
    """
        Number of waivers with type NOT_A_BUG by release.
    """


def get_total_fix_later_waivers():
    """
        Number of waivers with type FIX_LATER.
    """


def get_fix_later_waivers_by_release():
    """
        Number of waivers with type FIX_LATER by release.
    """



