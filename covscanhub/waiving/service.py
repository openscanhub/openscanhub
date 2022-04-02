# -*- coding: utf-8 -*-

"""
    compilation of functions that provide functionality for waiving and fill
    database with defects from scan
"""

from __future__ import absolute_import
import os
import re
import logging
import datetime
import tempfile
import shutil
import pipes
import pycsdiff

import json
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum

from covscancommon.constants import ERROR_DIFF_FILE, FIXED_DIFF_FILE,\
    DEFAULT_CHECKER_GROUP, SCAN_RESULTS_FILENAME
from .models import DEFECT_STATES, RESULT_GROUP_STATES, Defect, Result, \
    Checker, CheckerGroup, Waiver, ResultGroup, WaivingLog

from kobo.hub.models import Task
from kobo.shortcuts import run


logger = logging.getLogger(__name__)


__all__ = (
    'get_unwaived_rgs',
    'compare_result_groups',
    'get_last_waiver',
    'get_defects_diff_display',
    'display_in_result',
)


def find_processed_in_past(result):
    """
    When new scan is imported, check which defects were waived in past
    or marked as bugs.
    """

    # get all RGs, that does not have waiver
    for rg in get_unwaived_rgs(result):
        # was RG waived in past?
        w = get_last_waiver(
            rg.checker_group,
            rg.result.scanbinding.scan.package,
            rg.result.scanbinding.scan.tag.release,
            exclude=rg.id,
        )
        # compare defects in these 2 result groups using pycsdiff
        if w and compare_result_groups(rg, w.result_group):
            if w.is_bug():
                rg.set_bug_confirmed()
            else:
                # they match! -- change states
                rg.state = RESULT_GROUP_STATES['PREVIOUSLY_WAIVED']
                rg.defect_type = DEFECT_STATES['PREVIOUSLY_WAIVED']
                rg.save()

                #also changes states for defects
                for d in Defect.objects.filter(result_group=rg):
                    d.state = DEFECT_STATES['PREVIOUSLY_WAIVED']
                    d.save()


def get_unwaived_rgs(result):
    """
        Return ResultGroups that are not waived (and should be waived)
        for specific Result
    """
    return ResultGroup.objects.filter(result=result,
        state=RESULT_GROUP_STATES['NEEDS_INSPECTION'])


def assign_if_true(d, key, value):
    if bool(value):
        d[key] = value


def get_serializable_dict(query):
    result_dict = {}
    result_dict['defects'] = []
    for d in query:
        d_dict = {}
        d_dict['checker'] = d.checker.name
        assign_if_true(d_dict, 'annotation', d.annotation)
        assign_if_true(d_dict, 'defect_id', d.defect_identifier)
        assign_if_true(d_dict, 'function', d.function)
        d_dict['key_event_idx'] = d.key_event
        d_dict['events'] = d.events
        result_dict['defects'].append(d_dict)
    return result_dict


def compare_result_groups_shell(rg1, rg2):
    """
        Compare defects of two distinct result groups
        use csdiff tool - CLI interface
    """
    if rg1.defects_count != rg2.defects_count:
        return False
    return True
    rg1_defects = rg1.get_new_defects()
    rg2_defects = rg2.get_new_defects()

    dict1 = get_serializable_dict(rg1_defects)
    dict2 = get_serializable_dict(rg2_defects)

    tmp_dir = tempfile.mkdtemp(prefix="cs_diff")
    os.chmod(tmp_dir, 0o775)
    fd1, filename1 = tempfile.mkstemp(prefix='rg1', text=True, dir=tmp_dir)
    fd2, filename2 = tempfile.mkstemp(prefix='rg2', text=True, dir=tmp_dir)
    file1 = os.fdopen(fd1, 'w')
    json.dump(dict1, file1)
    file1.close()
    file2 = os.fdopen(fd2, 'w')
    json.dump(dict2, file2)
    file2.close()

    diff_cmd = ' '.join(['csdiff', '-j',
                         pipes.quote(os.path.join(tmp_dir, filename1)),
                         pipes.quote(os.path.join(tmp_dir, filename1)),
                         '>', 'result.js'])
    retcode, output = run(diff_cmd,
                          workdir=tmp_dir,
                          stdout=False,
                          can_fail=False,
                          logfile='csdiff.log',
                          return_stdout=False,
                          show_cmd=False)
    shutil.rmtree(tmp_dir)


def compare_result_groups(rg1, rg2):
    """
        Compare defects of two distinct result groups
        use csdiff tool -- python binding
    """
    if rg1.defects_count != rg2.defects_count:
        return False

    rg1_defects = rg1.get_new_defects()
    rg2_defects = rg2.get_new_defects()

    dict1 = get_serializable_dict(rg1_defects)
    dict2 = get_serializable_dict(rg2_defects)

    s1 = json.dumps(dict1)
    s2 = json.dumps(dict2)
    r_s1 = json.loads(pycsdiff.diff_scans(s1, s2))
    r_s2 = json.loads(pycsdiff.diff_scans(s2, s1))
    return not (r_s1['defects'] or r_s2['defects'])


def get_last_waiver(checker_group, package, release, exclude=None):
    """
    Try to get base waiver for specific checkergroup, package, release;
     return None if there is newer run with change in waiving;
    exclude specified resultgroup
    """
    waivers = Waiver.waivers.filter(
        result_group__checker_group=checker_group,
        result_group__result__scanbinding__scan__package=package,
        result_group__result__scanbinding__scan__tag__release=release,
    )
    if waivers:
        latest_waiver = waivers.latest()
        # return all RGs newer that latest_waiver's run, if these are changed
        # it means that last waiver is not valid
        rgs = ResultGroup.objects.filter(
            result__date_submitted__gt=
                latest_waiver.result_group.result.date_submitted,
            checker_group=latest_waiver.result_group.checker_group,
            result__scanbinding__scan__package=
                latest_waiver.result_group.result.scanbinding.scan.package,
            result__scanbinding__scan__tag__release=
                latest_waiver.result_group.result.scanbinding.scan.tag.release,
        ).exclude(id=exclude).values_list('state', flat=True).distinct()
        if RESULT_GROUP_STATES['NEEDS_INSPECTION'] in rgs:
            return None
        else:
            return latest_waiver
    else:
        return None


def get_first_result_group(checker_group, result, defect_type):
    """
    Return result group for same checker group, which is associated with
     previous scan (previous build of specified package)
    """
    first_sb = result.scanbinding.scan.get_first_scan_binding()
    if first_sb:
        if first_sb.result:
            try:
                return ResultGroup.objects.get(
                    checker_group=checker_group,
                    result=first_sb.result,
                    defect_type=defect_type,
                )
            except ObjectDoesNotExist:
                return None


def get_defects_diff(checker_group=None, result=None, defect_type=None,
                     rg=None):
    """
    diff between number of new defects from this scan and first one.
    Return None, if you dont have anything to diff against.

    @rtype: None or int
    @return: difference between defects
    """
    if rg is None:
        first_rg = get_first_result_group(checker_group, result, defect_type)
    else:
        first_rg = get_first_result_group(rg.checker_group, rg.result,
                                          rg.defect_type)
    # there is no first result group and there is actual one
    if first_rg is None and rg is not None:
        # is this scan first scan? If so, we dont need diff
        if rg.result.scanbinding.scan.get_child_scan():
            return rg.defects_count
        else:
            return None
    # there is first result group and there is no actual one
    elif first_rg is not None and rg is None:
        return first_rg.defects_count * -1
    elif first_rg is not None and rg is not None:
        return rg.defects_count - first_rg.defects_count
    else:
        return None


def get_defects_diff_display(response=None, checker_group=None,
                             result=None, defect_type=None, rg=None):
    if response is None:
        response = {}
    defects_diff = 0
    #defects_diff = get_defects_diff(checker_group=checker_group,
    #                                result=result,
    #                                defect_type=defect_type,
    #                                rg=rg)
    if defects_diff:  # not None & != 0
        if defect_type == DEFECT_STATES['NEW']:
            if defects_diff > 0:
                response['diff_state'] = 'defects_increased'
                response['diff_count'] = "%s%d" % ('+', defects_diff)
            elif defects_diff < 0:
                response['diff_state'] = 'defects_decreased'
                response['diff_count'] = "%d" % (defects_diff)
        elif defect_type == DEFECT_STATES['FIXED']:
            if defects_diff > 0:
                response['diff_state'] = 'defects_decreased'
                response['diff_count'] = "%s%d" % ('+', defects_diff)
            elif defects_diff < 0:
                response['diff_state'] = 'defects_increased'
                response['diff_count'] = "%d" % (defects_diff)
        elif defect_type == DEFECT_STATES['PREVIOUSLY_WAIVED']:
            response['diff_state'] = 'diff_state_neutral'
            if defects_diff > 0:
                response['diff_count'] = "%s%d" % ('+', defects_diff)
            elif defects_diff < 0:
                response['diff_count'] = "%d" % (defects_diff)
    return response


def get_defects_diff_display_by_rg(response, rg):
    return get_defects_diff_display(response,
                                    checker_group=rg.checker_group,
                                    result=rg.result,
                                    defect_type=rg.defect_type,
                                    rg=rg)


def display_in_result(rg):
    """
    return data that are displayed in waiver
    """
    response = {'group_state': rg.get_state_to_display()}
    response['defects_count'] = rg.defects_count
    response['defects_state'] = DEFECT_STATES.get_value(rg.defect_type)
    get_defects_diff_display_by_rg(response=response, rg=rg)
    return response


def waiver_condition(result_group):
    """placeholder for custom waiving conditions"""
    return bool(result_group.get_waivers())


def get_scans_new_defects_count(scan_id):
    """Return number of newly introduced bugs for particular scan"""
    rgs = ResultGroup.objects.filter(result__scanbinding__scan__id=scan_id,
                                     defect_type=DEFECT_STATES['NEW'])
    try:
        count = rgs.aggregate(Sum("defects_count"))['defects_count__sum']
    except KeyError:
        count = 0
    return count


def get_waivers_for_rg(rg):
    wls = WaivingLog.objects.for_rg(rg.id)
    if not wls:
        w = get_last_waiver(
            rg.checker_group,
            rg.result.scanbinding.scan.package,
            rg.result.scanbinding.scan.tag.release,
        )
        if w:
            return WaivingLog.objects.for_waiver(w)
    else:
        return wls


def apply_waiver(rg, sb, waiver):
    """
    rg -- processed result group
    sb -- scan binding
    waiver -- newly submitted waiver
    """
    if waiver_condition(rg):
        rg.apply_waiver(waiver)

        if not get_unwaived_rgs(sb.result):
            sb.scan.finalize()

"""
def waiver_condition(result_group):
    \"\"\"
    Function that contains condition for successfull waive -- there has to
    exist waiver from user who is in group 'qa' and 'devel'

    @param waivers_list: list of Waiver objects
    @type waivers_list: list

    @rtype: bool
    @return: True if condition holds and group is waived False otherwise
    \"\"\"
    #this should be in settings probably -- group names that users have to be
    #in to successfully waive
    required_groups = [u'qa', u'devel']
    ack_missing_from = set(required_groups)
    for waiver in result_group.get_waivers():
        ack_missing_from = ack_missing_from.difference(
            *waiver.user.groups.all().values_list('name')
        )
    return not bool(ack_missing_from)
"""
