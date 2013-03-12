# -*- coding: utf-8 -*-

"""
    Module that contains various statistics types. These functions are loaded
    dynamically. There is database record for each function.

    Functions get_*_by_release return dictionary with structure:
    {
        covscanhub.models.SystemRelease: value
    }
"""

import datetime

from kobo.hub.models import Task

from covscanhub.scan.models import Scan, SystemRelease,\
    ScanBinding, SCAN_TYPES_TARGET
from covscanhub.scan.service import diff_fixed_defects_in_package,\
    diff_fixed_defects_between_releases, diff_new_defects_between_releases

from covscanhub.waiving.models import Result, Defect, DEFECT_STATES, Waiver, \
    WAIVER_TYPES, ResultGroup, RESULT_GROUP_STATES

from django.db.models import Sum


#######
# SCANS
#######


def get_total_scans():
    """
        Scans count

        Number of all submitted scans.
    """
    return Scan.objects.filter(scan_type__in=SCAN_TYPES_TARGET).count()
get_total_scans.group = "SCANS"
get_total_scans.order = 1


def get_scans_by_release():
    """
        Scans count

        Number of submitted scans by release.
    """
    releases = SystemRelease.objects.filter(active=True)
    result = {}
    for r in releases:
        result[r] = Scan.objects.filter(scan_type__in=SCAN_TYPES_TARGET,
                                        tag__release=r.id).count()
    return result
get_scans_by_release.group = "SCANS"
get_scans_by_release.order = 1

#####
# LOC
#####


def get_total_lines():
    """
        Lines of code scanned

        Number of total lines of code scanned.
    """
    sbs = ScanBinding.objects.filter(scan__enabled=True)
    if not sbs:
        return 0
    else:
        return sbs.aggregate(Sum('result__lines'))['result__lines__sum']
get_total_lines.group = "LOC"
get_total_lines.order = 1

def get_lines_by_release():
    """
        Lines of code scanned

        Number of LoC scanned by RHEL release.
    """
    releases = SystemRelease.objects.filter(active=True)
    result = {}
    for r in releases:
        result[r] = ScanBinding.objects.filter(scan__enabled=True,
            scan__tag__release=r.id)\
            .aggregate(Sum('result__lines'))['result__lines__sum']
    return result
get_lines_by_release.group = "LOC"
get_lines_by_release.order = 1

#########
# DEFECTS
#########


def get_total_fixed_defects():
    """
        Fixed defects

        Number of defects that were marked as 'fixed'
    """
    return Defect.objects.filter(state=DEFECT_STATES['FIXED'],
        result_group__result__scanbinding__scan__enabled=True).count()
get_total_fixed_defects.group = "DEFECTS"
get_total_fixed_defects.order = 1

def get_fixed_defects_by_release():
    """
        Fixed defects

        Number of fixed defects found by release.
    """
    releases = SystemRelease.objects.filter(active=True)
    result = {}
    for r in releases:
        result[r] = Defect.objects.filter(
            result_group__result__scanbinding__scan__tag__release=r.id,
            state=DEFECT_STATES['FIXED'],
            result_group__result__scanbinding__scan__enabled=True
        ).count()
    return result
get_fixed_defects_by_release.group = "DEFECTS"
get_fixed_defects_by_release.order = 1


def get_total_new_defects():
    """
        New defects

        Number of newly introduced defects.
    """
    return Defect.objects.filter(state=DEFECT_STATES['NEW'],
        result_group__result__scanbinding__scan__enabled=True).count()
get_total_new_defects.group = "DEFECTS"
get_total_new_defects.order = 2


def get_new_defects_by_release():
    """
        New defects

        Number of newly introduced defects by release.
    """
    releases = SystemRelease.objects.filter(active=True)
    result = {}
    for r in releases:
        result[r] = Defect.objects.filter(
            result_group__result__scanbinding__scan__tag__release=r.id,
            state=DEFECT_STATES['NEW'],
            result_group__result__scanbinding__scan__enabled=True
        ).count()
    return result
get_new_defects_by_release.group = "DEFECTS"
get_new_defects_by_release.order = 2


def get_fixed_defects_in_release():
    """
        Fixed defects in one release

        Number of defects that were fixed between first scan and final one.
    """
    releases = SystemRelease.objects.filter(active=True)
    result = {}
    for r in releases:
        result[r] = 0
        for sb in ScanBinding.objects.filter(scan__tag__release=r.id,
                                             scan__enabled=True):
            result[r] += diff_fixed_defects_in_package(sb)
    return result
get_fixed_defects_in_release.group = "DEFECTS"
get_fixed_defects_in_release.order = 3


def get_fixed_defects_between_releases():
    """
        Fixed defects between releases

        Number of defects that were fixed between this release and previous one
    """
    releases = SystemRelease.objects.filter(active=True, systemrelease=False)
    result = {}
    for r in releases:
        result[r] = 0
        for sb in ScanBinding.objects.filter(scan__tag__release=r.id,
                                             scan__enabled=True):
            result[r] += diff_fixed_defects_between_releases(sb)
    return result
get_fixed_defects_between_releases.group = "DEFECTS"
get_fixed_defects_between_releases.order = 4


def get_new_defects_between_releases():
    """
        New defects between releases

        Number of newly added defects between this release and previous one
    """
    releases = SystemRelease.objects.filter(active=True)
    result = {}
    for r in releases:
        result[r] = 0
        for sb in ScanBinding.objects.filter(scan__tag__release=r.id,
                                             scan__enabled=True):
            result[r] += diff_new_defects_between_releases(sb)
    return result
get_new_defects_between_releases.group = "DEFECTS"
get_new_defects_between_releases.order = 5

#########
# WAIVERS
#########


def get_total_waivers_submitted():
    """
        Waivers submitted

        Number of waivers submitted. (including invalidated)
    """
    return Waiver.objects.all().count()
get_total_waivers_submitted.order = 1
get_total_waivers_submitted.group = "WAIVERS"


def get_waivers_submitted_by_release():
    """
        Waivers submitted

        Number of waivers submitted by release. (including invalidated)
    """
    releases = SystemRelease.objects.filter(active=True)
    result = {}
    for r in releases:
        result[r] = Waiver.objects.filter(
            result_group__result__scanbinding__scan__tag__release=r.id,
        ).count()
    return result
get_waivers_submitted_by_release.group = "WAIVERS"
get_waivers_submitted_by_release.order = 1


def get_total_missing_waivers():
    """
        Missing waivers

        Number of groups that were not waived, but should have been.
    """
    return ResultGroup.objects.filter(
        result__scanbinding__scan__enabled=True,
        state=RESULT_GROUP_STATES['NEEDS_INSPECTION']).count()
get_total_missing_waivers.group = "WAIVERS"
get_total_missing_waivers.order = 2


def get_missing_waivers_by_release():
    """
        Missing waivers

        Number of groups that were not waived by release.
    """
    releases = SystemRelease.objects.filter(active=True)
    result = {}
    for r in releases:
        result[r] = ResultGroup.objects.filter(
            state=RESULT_GROUP_STATES['NEEDS_INSPECTION'],
            result__scanbinding__scan__tag__release=r.id,
            result__scanbinding__scan__enabled=True,
        ).count()
    return result
get_missing_waivers_by_release.group = "WAIVERS"
get_missing_waivers_by_release.order = 2


def get_total_is_a_bug_waivers():
    """
        'is a bug' waivers

        Number of waivers with type IS_A_BUG.
    """
    return Waiver.objects.filter(state=WAIVER_TYPES['IS_A_BUG'],
                                 is_deleted=False).count()
get_total_is_a_bug_waivers.group = "WAIVERS"
get_total_is_a_bug_waivers.order = 3


def get_is_a_bug_waivers_by_release():
    """
        'is a bug' waivers

        Number of waivers with type IS_A_BUG by release.
    """
    releases = SystemRelease.objects.filter(active=True)
    result = {}
    for r in releases:
        result[r] = Waiver.objects.filter(
            state=WAIVER_TYPES['IS_A_BUG'],
            result_group__result__scanbinding__scan__tag__release=r.id,
            is_deleted=False,
        ).count()
    return result
get_is_a_bug_waivers_by_release.group = "WAIVERS"
get_is_a_bug_waivers_by_release.order = 3


def get_total_not_a_bug_waivers():
    """
        'not a bug' waivers

        Number of waivers with type NOT_A_BUG.
    """
    return Waiver.objects.filter(state=WAIVER_TYPES['NOT_A_BUG'],
                                 is_deleted=False,).count()
get_total_not_a_bug_waivers.group = "WAIVERS"
get_total_not_a_bug_waivers.order = 4


def get_not_a_bug_waivers_by_release():
    """
        'not a bug' waivers

        Number of waivers with type NOT_A_BUG by release.
    """
    releases = SystemRelease.objects.filter(active=True)
    result = {}
    for r in releases:
        result[r] = Waiver.objects.filter(
            state=WAIVER_TYPES['NOT_A_BUG'],
            result_group__result__scanbinding__scan__tag__release=r.id,
            is_deleted=False,
        ).count()
    return result
get_not_a_bug_waivers_by_release.group = "WAIVERS"
get_not_a_bug_waivers_by_release.order = 4


def get_total_fix_later_waivers():
    """
        'fix later' waivers

        Number of waivers with type FIX_LATER.
    """
    return Waiver.objects.filter(state=WAIVER_TYPES['FIX_LATER'],
                                 is_deleted=False,).count()
get_total_fix_later_waivers.group = "WAIVERS"
get_total_fix_later_waivers.order = 5


def get_fix_later_waivers_by_release():
    """
        'fix later' waivers

        Number of waivers with type FIX_LATER by release.
    """
    releases = SystemRelease.objects.filter(active=True)
    result = {}
    for r in releases:
        result[r] = Waiver.objects.filter(
            state=WAIVER_TYPES['FIX_LATER'],
            result_group__result__scanbinding__scan__tag__release=r.id,
            is_deleted=False,
        ).count()
    return result
get_fix_later_waivers_by_release.group = "WAIVERS"
get_fix_later_waivers_by_release.order = 5

######
# TIME
######


def get_busy_minutes():
    """
        Busy minutes

        Number of minutes during the system was busy.
    """
    result = datetime.timedelta()
    for t in Task.objects.all():
        try:
            result += t.time
        except TypeError:
            pass
    return result.seconds / 60
get_busy_minutes.order = 1
get_busy_minutes.group = "TIME"


def get_minutes_spent_scanning():
    """
        Scanning minutes

        Number of minutes that system spent scanning.
    """
    result = Result.objects.all()
    if not result:
        return 0
    else:
        return result.aggregate(Sum('scanning_time'))['scanning_time__sum'] / 60
get_minutes_spent_scanning.group = "TIME"
get_minutes_spent_scanning.order = 2
