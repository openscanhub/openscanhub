# -*- coding: utf-8 -*-

"""
    Module that contains various statistics types. These functions are loaded
    dynamically. There is database record for each function.

    Functions get_*_by_release return dictionary with structure:
    {
        covscanhub.models.SystemRelease: value        
    }
"""

from covscanhub.scan.models import Scan, SystemRelease, SCAN_TYPES
from covscanhub.scan.service import diff_fixed_defects_in_package
from covscanhub.waiving.models import Result, Defect, DEFECT_STATES, Waiver, \
    WAIVER_TYPES, ResultGroup, RESULT_GROUP_STATES

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
    for r in releases:
        result[r.id] = Scan.objects.filter(scan_type=SCAN_TYPES['ERRATA'],
                                           tag__release=r.id).count()
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
    for r in releases:
        result[r.id] = Result.objects.filter(scan__tag__release=r.id)\
                        .aggregate(Sum('lines'))['lines__sum']
    return result

#########
# DEFECTS
#########


def get_total_fixed_defects():
    """
        Number of fixed defects found.
    """
    return Defect.objects.filter(state=DEFECT_STATES['FIXED'],
                                 result_group__result__scan__enabled=True)\
                                 .count()


def get_fixed_defects_by_release():
    """
        Number of fixed defects found by release.
    """
    releases = SystemRelease.objects.all()
    result = {}
    for r in releases:
        result[r.id] = Defect.objects.filter(
            result_group__result__scan__tag__release=r.id,
            state=DEFECT_STATES['FIXED'],
            result_group__result__scan__enabled=True
        ).count()
    return result


def get_total_new_defects():
    """
        Number of newly introduced defects.
    """
    return Defect.objects.filter(state=DEFECT_STATES['NEW'],
                                 result_group__result__scan__enabled=True)\
                                 .count()


def get_new_defects_by_release():
    """
        Number of newly introduced defects by release.
    """
    releases = SystemRelease.objects.all()
    result = {}
    for r in releases:
        result[r.id] = Defect.objects.filter(
            result_group__result__scan__tag__release=r.id,
            state=DEFECT_STATES['NEW'],
            result_group__result__scan__enabled=True
        ).count()
    return result


def get_fixed_defects_between_releases():
    """
        Number of defects that were fixed between first scan and final one
    """
    releases = SystemRelease.objects.all()
    result = {}
    for r in releases:
        result[r.id] = 0
        for s in Scan.objects.filter(tag__release=r.id, enabled=True):
            result[r.id] += diff_fixed_defects_in_package(s)
    return result    

#########
# WAIVERS
#########


def get_total_waivers_submitted():
    """
        Number of waivers submitted.
    """
    return Waiver.objects.all().count()


def get_waivers_submitted_by_release():
    """
        Number of waivers submitted by release.
    """
    releases = SystemRelease.objects.all()
    result = {}
    for r in releases:
        result[r.id] = Waiver.objects.filter(
            result_group__result__scan__tag__release=r.id,
        ).count()
    return result


def get_total_missing_waivers():
    """
        Number of tests that were not waived, but should have been.
    """
    return ResultGroup.objects.filter(
        state=RESULT_GROUP_STATES['NEEDS_INSPECTION']).count


def get_total_missing_waivers_by_release():
    """
        Number of tests that were not waived by release.
    """
    releases = SystemRelease.objects.all()
    result = {}
    for r in releases:
        result[r.id] = ResultGroup.objects.filter(
            state=RESULT_GROUP_STATES['NEEDS_INSPECTION'],
            result__scan__tag__release=r.id,
        ).count()
    return result


def get_total_is_a_bug_waivers():
    """
        Number of waivers with type IS_A_BUG.
    """
    return Waiver.objects.filter(state=WAIVER_TYPES['IS_A_BUG']).count()


def get_is_a_bug_waivers_by_release():
    """
        Number of waivers with type IS_A_BUG by release.
    """
    releases = SystemRelease.objects.all()
    result = {}
    for r in releases:
        result[r.id] = Waiver.objects.filter(
            state=WAIVER_TYPES['IS_A_BUG'],
            result_group__result__scan__tag__release=r.id,
        ).count()
    return result


def get_total_not_a_bug_waivers():
    """
        Number of waivers with type NOT_A_BUG.
    """
    return Waiver.objects.filter(state=WAIVER_TYPES['NOT_A_BUG']).count()


def get_not_a_bug_waivers_by_release():
    """
        Number of waivers with type NOT_A_BUG by release.
    """
    releases = SystemRelease.objects.all()
    result = {}
    for r in releases:
        result[r.id] = Waiver.objects.filter(
            state=WAIVER_TYPES['NOT_A_BUG'],
            result_group__result__scan__tag__release=r.id,
        ).count()
    return result


def get_total_fix_later_waivers():
    """
        Number of waivers with type FIX_LATER.
    """
    return Waiver.objects.filter(state=WAIVER_TYPES['FIX_LATER']).count()


def get_fix_later_waivers_by_release():
    """
        Number of waivers with type FIX_LATER by release.
    """
    releases = SystemRelease.objects.all()
    result = {}
    for r in releases:
        result[r.id] = Waiver.objects.filter(
            state=WAIVER_TYPES['FIX_LATER'],
            result_group__result__scan__tag__release=r.id,
        ).count()
    return result