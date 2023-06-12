# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

"""
    Module that contains various statistics types. These functions are loaded
    dynamically. There is database record for each function.

    Functions get_*_by_release return dictionary with structure:
    {
        osh.hub.scan.models.SystemRelease: value
    }
"""

import datetime

from django.db.models import Sum
from kobo.hub.models import Task

from osh.hub.scan.models import Scan, ScanBinding, SystemRelease
from osh.hub.scan.service import (diff_fixed_defects_between_releases,
                                  diff_fixed_defects_in_package,
                                  diff_new_defects_between_releases,
                                  diff_new_defects_in_package)
from osh.hub.stats.utils import stat_function
from osh.hub.waiving.models import Defect, Result, ResultGroup, Waiver

#######
# SCANS
#######


@stat_function(1, "SCANS", "Scans count",
               "Number of all submitted scans.")
def get_total_scans():
    return Scan.objects.enabled().target().count()


@stat_function(1, "SCANS", "Scans count",
               "Number of submitted scans by release.")
def get_scans_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Scan.objects.enabled().target().by_release(r).count()
            for r in releases}


@stat_function(2, "SCANS", "Rebase scans count",
               "Number of all submitted scans of rebases.")
def get_rebases_count():
    return Scan.objects.rebases().count()


@stat_function(2, "SCANS", "Rebase scans count",
               "Number of all submitted scans of rebases by release.")
def get_rebases_count_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Scan.objects.rebases().by_release(r).count() for r in releases}


@stat_function(3, "SCANS", "New package scans count",
               "Number of scans of new packages.")
def get_newpkg_count():
    return Scan.objects.newpkgs().count()


@stat_function(3, "SCANS", "New package scans count",
               "Number of scans of new packages by release.")
def get_newpkg_count_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Scan.objects.newpkgs().by_release(r).count() for r in releases}


@stat_function(4, "SCANS", "Update scans count",
               "Number of scans of updates.")
def get_updates_count():
    return Scan.objects.updates().count()


@stat_function(4, "SCANS", "Update scans count",
               "Number of scans of updates by release.")
def get_updates_count_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Scan.objects.updates().by_release(r).count() for r in releases}

#####
# LOC
#####


@stat_function(1, "LOC", "Lines of code scanned",
               "Number of total lines of code scanned.")
def get_total_lines():
    """
    """
    sbs = ScanBinding.objects.enabled()
    return sbs.aggregate(sum=Sum('result__lines'))['sum'] or 0


@stat_function(1, "LOC", "Lines of code scanned",
               "Number of LoC scanned by RHEL release.")
def get_lines_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: ScanBinding.objects.enabled().by_release(r)
            .aggregate(sum=Sum('result__lines'))['sum'] or 0
            for r in releases}

#########
# DEFECTS
#########


@stat_function(1, "DEFECTS", "Fixed defects",
               "Number of defects that were marked as 'fixed'.")
def get_total_fixed_defects():
    return Defect.objects.enabled().fixed().count()


@stat_function(1, "DEFECTS", "Fixed defects",
               "Number of fixed defects found by release.")
def get_fixed_defects_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Defect.objects.enabled().by_release(r).fixed().count()
            for r in releases}


@stat_function(2, "DEFECTS", "Fixed defects in rebases",
               "Number of defects that were marked as 'fixed' in rebases.")
def get_total_fixed_defects_in_rebases():
    return Defect.objects.enabled().rebases().fixed().count()


@stat_function(2, "DEFECTS", "Fixed defects in rebases",
               "Number of fixed defects found in rebases by release.")
def get_fixed_defects_in_rebases_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Defect.objects.enabled().rebases().by_release(r).fixed().count()
            for r in releases}


@stat_function(3, "DEFECTS", "Fixed defects in updates",
               "Number of defects that were marked as 'fixed' in updates.")
def get_total_fixed_defects_in_updates():
    return Defect.objects.enabled().updates().fixed().count()


@stat_function(3, "DEFECTS", "Fixed defects in updates",
               "Number of fixed defects found in updates by release.")
def get_fixed_defects_in_updates_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Defect.objects.enabled().updates().by_release(r).fixed().count()
            for r in releases}


@stat_function(4, "DEFECTS", "New defects",
               "Number of newly introduced defects.")
def get_total_new_defects():
    return Defect.objects.enabled().new().count()


@stat_function(4, "DEFECTS", "New defects",
               "Number of newly introduced defects by release.")
def get_new_defects_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Defect.objects.enabled().by_release(r).new().count()
            for r in releases}


@stat_function(5, "DEFECTS", "New defects in rebases",
               "Number of newly introduced defects in rebases.")
def get_total_new_defects_in_rebases():
    return Defect.objects.enabled().rebases().new().count()


@stat_function(5, "DEFECTS", "New defects in rebases",
               "Number of newly introduced defects in rebases by release.")
def get_new_defects_in_rebases_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Defect.objects.enabled().rebases().by_release(r).new().count()
            for r in releases}


@stat_function(6, "DEFECTS", "New defects in updates",
               "Number of newly introduced defects in updates.")
def get_total_new_defects_in_updates():
    return Defect.objects.enabled().updates().new().count()


@stat_function(6, "DEFECTS", "New defects in updates",
               "Number of newly introduced defects in updates by release.")
def get_new_defects_in_updates_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Defect.objects.enabled().updates().by_release(r).new().count()
            for r in releases}


@stat_function(8, "DEFECTS", "Eliminated newly introduced defects in rebases",
               "Number of newly introduced defects in rebases that were fixed between first scan and final one.")
def get_eliminated_in_rebases_in_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: sum(diff_new_defects_in_package(sb) for sb in
                   ScanBinding.objects.by_release(r).rebases().enabled())
            for r in releases}


@stat_function(9, "DEFECTS", "Eliminated newly introduced defects in new packages",
               "Number of newly introduced defects in new packages that were fixed between first scan and final one.")
def get_eliminated_in_newpkgs_in_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: sum(diff_new_defects_in_package(sb) for sb in
                   ScanBinding.objects.by_release(r).newpkgs().enabled())
            for r in releases}


@stat_function(10, "DEFECTS", "Eliminated newly introduced defects in updates",
               "Number of newly introduced defects in updates that were fixed between first scan and final one.")
def get_eliminated_in_updates_in_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: sum(diff_new_defects_in_package(sb) for sb in
                   ScanBinding.objects.by_release(r).updates().enabled())
            for r in releases}


@stat_function(11, "DEFECTS", "Fixed defects in one release",
               "Number of defects that were fixed between first scan and final one.")
def get_fixed_defects_in_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: sum(diff_fixed_defects_in_package(sb) for sb in
                   ScanBinding.objects.by_release(r).enabled())
            for r in releases}


@stat_function(12, "DEFECTS", "Fixed defects between releases",
               "Number of defects that were fixed between this release and previous one")
def get_fixed_defects_between_releases():
    releases = SystemRelease.objects.filter(active=True,
                                            systemrelease__isnull=False)
    return {r: sum(diff_fixed_defects_between_releases(sb) for sb in
                   ScanBinding.objects.by_release(r).enabled())
            for r in releases}


@stat_function(13, "DEFECTS", "New defects between releases",
               "Number of newly added defects between this release and previous one")
def get_new_defects_between_releases():
    releases = SystemRelease.objects.filter(active=True)
    return {r: sum(diff_new_defects_between_releases(sb) for sb in
                   ScanBinding.objects.by_release(r).enabled())
            for r in releases}

#########
# WAIVERS
#########


@stat_function(1, "WAIVERS", "Waivers submitted",
               "Number of waivers submitted. (including invalidated)")
def get_total_waivers_submitted():
    return Waiver.waivers.all().count()


@stat_function(1, "WAIVERS", "Waivers submitted",
               "Number of waivers submitted by release. (including invalidated)")
def get_waivers_submitted_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Waiver.waivers.by_release(r).count() for r in releases}


@stat_function(2, "WAIVERS", "Waivers submitted for regular updates",
               "Number of waivers submitted for regular updates.")
def get_total_update_waivers_submitted():
    return Waiver.waivers.updates().count()


@stat_function(2, "WAIVERS", "Waivers submitted for regular updates",
               "Number of waivers submitted for updates in this release.")
def get_total_update_waivers_submitted_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Waiver.waivers.updates().by_release(r).count()
            for r in releases}


@stat_function(3, "WAIVERS", "Waivers submitted for rebases",
               "Number of waivers submitted for rebases.")
def get_total_rebase_waivers_submitted():
    return Waiver.waivers.rebases().count()


@stat_function(3, "WAIVERS", "Waivers submitted for rebases",
               "Number of waivers submitted for rebases in this release.")
def get_total_rebase_waivers_submitted_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Waiver.waivers.rebases().by_release(r).count()
            for r in releases}


@stat_function(4, "WAIVERS", "Waivers submitted for newpkg scans",
               "Number of waivers submitted for new package scans.")
def get_total_newpkg_waivers_submitted():
    return Waiver.waivers.newpkgs().count()


@stat_function(4, "WAIVERS", "Waivers submitted for newpkg scans",
               "Number of waivers submitted for new package scans in this release.")
def get_total_newpkg_waivers_submitted_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Waiver.waivers.newpkgs().by_release(r).count()
            for r in releases}


@stat_function(5, "WAIVERS", "Missing waivers",
               "Number of groups that were not waived, but should have been.")
def get_total_missing_waivers():
    return ResultGroup.objects.missing_waiver().count()


@stat_function(5, "WAIVERS", "Missing waivers",
               "Number of groups that were not waived by release.")
def get_missing_waivers_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: ResultGroup.objects.missing_waiver().by_release(r).count()
            for r in releases}


@stat_function(6, "WAIVERS", "Missing waivers in rebases",
               "Number of groups in rebases that were not waived, but should have been.")
def get_total_missing_waivers_in_rebases():
    return ResultGroup.objects.missing_waiver().rebases().count()


@stat_function(6, "WAIVERS", "Missing waivers in rebases",
               "Number of groups in rebases that were not waived by release.")
def get_missing_waivers_in_rebases_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: ResultGroup.objects.missing_waiver().rebases().by_release(r).count()
            for r in releases}


@stat_function(7, "WAIVERS", "Missing waivers in new packages",
               "Number of groups in new package scans that were not waived.")
def get_total_missing_waivers_in_newpkgs():
    return ResultGroup.objects.missing_waiver().newpkgs().count()


@stat_function(7, "WAIVERS", "Missing waivers in new packages",
               "Number of groups in new package scans that were not waived by release.")
def get_missing_waivers_in_newpkgs_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: ResultGroup.objects.missing_waiver().newpkgs().by_release(r).count()
            for r in releases}


@stat_function(8, "WAIVERS", "Missing waivers in updates",
               "Number of groups in updates that were not waived.")
def get_total_missing_waivers_in_updates():
    return ResultGroup.objects.missing_waiver().updates().count()


@stat_function(8, "WAIVERS", "Missing waivers in updates",
               "Number of groups in updates that were not waived.")
def get_missing_waivers_in_updates_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: ResultGroup.objects.missing_waiver().updates().by_release(r).count()
            for r in releases}


@stat_function(9, "WAIVERS", "'is a bug' waivers",
               "Number of waivers with type IS_A_BUG.")
def get_total_is_a_bug_waivers():
    return Waiver.waivers.is_a_bugs().count()


@stat_function(9, "WAIVERS", "'is a bug' waivers",
               "Number of waivers with type IS_A_BUG by release.")
def get_is_a_bug_waivers_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Waiver.waivers.is_a_bugs().by_release(r).count()
            for r in releases}


@stat_function(10, "WAIVERS", "'is a bug' waivers in rebases",
               "Number of waivers with type IS_A_BUG in rebases by release.")
def get_is_a_bug_waivers_in_rebases_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Waiver.waivers.is_a_bugs().rebases().by_release(r).count()
            for r in releases}


@stat_function(11, "WAIVERS", "'is a bug' waivers in newpkgs",
               "Number of waivers with type IS_A_BUG in new packages by release.")
def get_is_a_bug_waivers_in_newpkgs_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Waiver.waivers.is_a_bugs().newpkgs().by_release(r).count()
            for r in releases}


@stat_function(12, "WAIVERS", "'is a bug' waivers in updates",
               "Number of waivers with type IS_A_BUG in updates by release.")
def get_is_a_bug_waivers_in_updates_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Waiver.waivers.is_a_bugs().updates().by_release(r).count()
            for r in releases}


@stat_function(10, "WAIVERS", "'not a bug' waivers",
               "Number of waivers with type NOT_A_BUG.")
def get_total_not_a_bug_waivers():
    return Waiver.waivers.not_a_bugs().count()


@stat_function(13, "WAIVERS", "'not a bug' waivers",
               "Number of waivers with type NOT_A_BUG by release.")
def get_not_a_bug_waivers_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Waiver.waivers.not_a_bugs().by_release(r).count()
            for r in releases}


@stat_function(14, "WAIVERS", "'not a bug' waivers in rebases",
               "Number of waivers with type NOT_A_BUG in rebases by release.")
def get_not_a_bug_waivers_in_rebases_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Waiver.waivers.not_a_bugs().rebases().by_release(r).count()
            for r in releases}


@stat_function(15, "WAIVERS", "'not a bug' waivers in newpkgs",
               "Number of waivers with type NOT_A_BUG in new packages by release.")
def get_not_a_bug_waivers_in_newpkgs_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Waiver.waivers.not_a_bugs().newpkgs().by_release(r).count()
            for r in releases}


@stat_function(16, "WAIVERS", "'not a bug' waivers in updates",
               "Number of waivers with type NOT_A_BUG in updates by release.")
def get_not_a_bug_waivers_in_updates_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Waiver.waivers.not_a_bugs().updates().by_release(r).count()
            for r in releases}


@stat_function(11, "WAIVERS", "'fix later' waivers",
               "Number of waivers with type FIX_LATER.")
def get_total_fix_later_waivers():
    return Waiver.waivers.fix_laters().count()


@stat_function(17, "WAIVERS", "'fix later' waivers",
               "Number of waivers with type FIX_LATER by release.")
def get_fix_later_waivers_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Waiver.waivers.fix_laters().by_release(r).count()
            for r in releases}


@stat_function(18, "WAIVERS", "'fix later' waivers in rebases",
               "Number of waivers with type FIX_LATER in rebases by release.")
def get_fix_later_waivers_in_rebases_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Waiver.waivers.fix_laters().rebases().by_release(r).count()
            for r in releases}


@stat_function(19, "WAIVERS", "'fix later' waivers in newpkgs",
               "Number of waivers with type FIX_LATER in new packages by release.")
def get_fix_later_waivers_in_newpkgs_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Waiver.waivers.fix_laters().newpkgs().by_release(r).count()
            for r in releases}


@stat_function(20, "WAIVERS", "'fix later' waivers in updates",
               "Number of waivers with type FIX_LATER in updates by release.")
def get_fix_later_waivers_in_updates_by_release():
    releases = SystemRelease.objects.filter(active=True)
    return {r: Waiver.waivers.fix_laters().updates().by_release(r).count()
            for r in releases}

######
# TIME
######


@stat_function(1, "TIME", "Busy minutes",
               "Number of minutes during the system was busy.")
def get_busy_minutes():
    result = datetime.timedelta()
    for t in Task.objects.all():
        result += t.time or datetime.timedelta()
    return int(result.total_seconds() // 60)


@stat_function(2, "TIME", "Scanning minutes",
               "Number of minutes that system spent scanning.")
def get_minutes_spent_scanning():
    results = Result.objects.all()

    # TODO: Django 4 introduced default kwarg for the value of an empty Sum,
    # e.g. Sum over an empty QuerySet or only a field with Null values
    sum = results.aggregate(sum=Sum('scanning_time'))['sum'] or 0
    return sum // 60
