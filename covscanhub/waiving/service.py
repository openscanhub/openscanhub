# -*- coding: utf-8 -*-

"""
    compilation of functions that provide functionality for waiving and fill
    database with defects from scan
"""

import os
import re
import logging
import datetime
import tempfile
import shutil
import pipes
import pycsdiff

import django.utils.simplejson as json
from django.core.exceptions import ObjectDoesNotExist

from covscanhub.other.constants import ERROR_DIFF_FILE, FIXED_DIFF_FILE,\
    DEFAULT_CHECKER_GROUP
from models import DEFECT_STATES, RESULT_GROUP_STATES, Defect, Result, \
    Checker, CheckerGroup, Waiver, ResultGroup

from kobo.hub.models import Task
from kobo.shortcuts import run


logger = logging.getLogger(__name__)


__all__ = (
    'create_results',
    'get_unwaived_rgs',
    'compare_result_groups',
    'get_last_waiver',
    'update_analyzer',
    'load_defects_from_json',
    'get_defects_diff_display',
    'display_in_result',
)


def load_defects_from_json(json_dict, result,
                           defect_state=DEFECT_STATES['UNKNOWN']):
    """
    this function loads defects from provided json dictionary and writes them
    into provided result model object
    """
    if 'defects' in json_dict:
        for defect in json_dict['defects']:
            d = Defect()
            json_checker_name = defect['checker']
            try:
                # get_or_create fails here, because there will be integrity
                # error on group atribute
                checker = Checker.objects.get(name=json_checker_name)
            except ObjectDoesNotExist:
                checker = Checker()
                checker.group = CheckerGroup.objects.get(
                    name=DEFAULT_CHECKER_GROUP)
                checker.name = json_checker_name
                checker.save()

            rg, created = ResultGroup.objects.get_or_create(
                checker_group=checker.group,
                result=result,
                defect_type=defect_state)

            if rg.state == RESULT_GROUP_STATES['UNKNOWN']:
                if defect_state == DEFECT_STATES['NEW']:
                    rg.state = RESULT_GROUP_STATES['NEEDS_INSPECTION']
                elif defect_state == DEFECT_STATES['FIXED']:
                    rg.state = RESULT_GROUP_STATES['INFO']

            rg.defects_count += 1
            rg.save()

            d.checker = checker
            d.result_group = rg
            d.annotation = defect.get('annotation', None)
            d.defect_identifier = defect.get('defect_id', None)
            d.function = defect.get('function', None)
            d.result = result
            d.state = defect_state
            d.key_event = defect['key_event_idx']
            d.events = defect['events']
            d.save()


def load_defects_from_file(file_path, result, defect_state):
    try:
        fd = open(file_path, 'r')
    except IOError:
        logger.critical('Unable to open file %s', file_path)
        return
    js = json.load(fd)
    load_defects_from_json(js, result, defect_state)
    fd.close()


def update_analyzer(result, json_dict):
    """
    fills object result with information about which analyzer performed scan
    """
    if 'scan' in json_dict:
        if 'analyzer' in json_dict['scan']:
            result.scanner = json_dict['scan']['analyzer']
        if 'analyzer-version' in json_dict['scan']:
            version = json_dict['scan']['analyzer-version']
            pattern = r'version (?P<version>\d{1,2}\.\d{1,2}\.\d{1,2})'
            p_version = re.search(pattern, version)
            if p_version:
                result.scanner_version = p_version.group('version')
            else:
                pattern2 = r'^(?P<version>\d{1,2}\.\d{1,2}\.\d{1,2})'
                p2_version = re.search(pattern2, version)
                if p2_version:
                    result.scanner_version = p2_version.group('version')
                else:
                    result.scanner_version = version
        if 'lines-processed' in json_dict['scan']:
            result.lines = int(json_dict['scan']['lines-processed'])
        elif 'lines_processed' in json_dict['scan']:
            result.lines = int(json_dict['scan']['lines_processed'])
        if 'time-elapsed-analysis' in json_dict['scan']:
            t = datetime.datetime.strptime(
                json_dict['scan']['time-elapsed-analysis'],
                "%H:%M:%S")
            time_delta = datetime.timedelta(hours=t.hour,
                                            minutes=t.minute,
                                            seconds=t.second)
            result.scanning_time = int(time_delta.days * 86400 +
                                       time_delta.seconds)
    result.save()


def create_results(scan, sb):
    """
    Task finished, so this method should update results
    """
    logger.debug('Creating results for scan %s', scan)
    task_dir = Task.get_task_dir(sb.task.id)

    #json's path is <TASK_DIR>/<NVR>/run1/<NVR>.js
    defects_path = os.path.join(task_dir, scan.nvr, 'run1', scan.nvr + '.js')
    fixed_file_path = os.path.join(task_dir, FIXED_DIFF_FILE)
    diff_file_path = os.path.join(task_dir, ERROR_DIFF_FILE)

    try:
        f = open(defects_path, 'r')
    except IOError:
        logger.critical('Unable to open defects file %s', defects_path)
        return
    json_dict = json.load(f)

    r = Result()

    update_analyzer(r, json_dict)

    r.save()

    sb.result = r
    sb.save()

    f.close()

    if scan.is_errata_scan():
        if scan.is_newpkg_scan():
            load_defects_from_file(defects_path, r, DEFECT_STATES['NEW'])
        else:
            load_defects_from_file(fixed_file_path, r, DEFECT_STATES['FIXED'])
            load_defects_from_file(diff_file_path, r, DEFECT_STATES['NEW'])

            for rg in get_unwaived_rgs(r):
                w = get_last_waiver(
                    rg.checker_group,
                    rg.result.scanbinding.scan.package,
                    rg.result.scanbinding.scan.tag.release,
                )
                if w and compare_result_groups(rg, w.result_group):
                    rg.state = RESULT_GROUP_STATES['PREVIOUSLY_WAIVED']
                    rg.defect_type = DEFECT_STATES['PREVIOUSLY_WAIVED']
                    rg.save()

        for rg in ResultGroup.objects.filter(result=r):
            counter = 1
            for defect in Defect.objects.filter(result_group=rg):
                defect.order = counter
                defect.save()
                counter += 1
    return r


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
    os.chmod(tmp_dir, 0775)
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


def get_last_waiver(checker_group, package, release):
    """
    Try to get base waiver for specific checkergroup, package, release
    """
    waivers = Waiver.objects.filter(
        result_group__checker_group=checker_group,
        result_group__result__scanbinding__scan__package=package,
        result_group__result__scanbinding__scan__tag__release=release,
        is_deleted=False,
    )
    if waivers:
        return waivers.latest()
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
    defects_diff = get_defects_diff(checker_group=checker_group,
                                    result=result,
                                    defect_type=defect_type,
                                    rg=rg)
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
