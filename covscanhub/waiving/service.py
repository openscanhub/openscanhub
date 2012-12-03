# -*- coding: utf-8 -*-

"""
    compilation of functions that provide functionality for waiving and fill
    database with defects from scan
"""

import os
import re
import logging
import datetime

import django.utils.simplejson as json
from django.core.exceptions import ObjectDoesNotExist

from covscanhub.other.constants import ERROR_DIFF_FILE, FIXED_DIFF_FILE,\
    DEFAULT_CHECKER_GROUP
from models import DEFECT_STATES, RESULT_GROUP_STATES, Defect, Result, \
    Checker, CheckerGroup, Waiver, ResultGroup

from kobo.hub.models import Task


logger = logging.getLogger(__name__)


__all__ = (
    'create_results',
    'get_unwaived_rgs',
    'compare_result_groups',
    'get_last_waiver',
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

            if defect_state == DEFECT_STATES['NEW']:
                rg.new_defects += 1
            elif defect_state == DEFECT_STATES['FIXED']:
                rg.fixed_defects += 1
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
            time_delta = datetime.timedelta(days=t.day,
                                            hours=t.hour,
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
        try:
            fixed_file = open(fixed_file_path, 'r')
        except IOError:
            print 'Unable to open file %s' % fixed_file_path
            return
        fixed_json_dict = json.load(fixed_file)
        load_defects_from_json(fixed_json_dict, r, DEFECT_STATES['FIXED'])
        fixed_file.close()

        try:
            diff_file = open(diff_file_path, 'r')
        except IOError:
            print 'Unable to open file %s' % diff_file_path
            return
        diff_json_dict = json.load(diff_file)
        load_defects_from_json(diff_json_dict, r, DEFECT_STATES['NEW'])
        diff_file.close()

        for rg in ResultGroup.objects.filter(result=r):
            counter = 1
            for defect in Defect.objects.filter(result_group=rg):
                defect.order = counter
                defect.save()
                counter += 1

        for rg in get_unwaived_rgs(r):
            w = get_last_waiver(
                rg.checker_group,
                rg.result.scanbinding.scan.package,
                rg.result.scanbinding.scan.tag.release,
            )
            if w and compare_result_groups(rg, w.result_group):
                rg.state = RESULT_GROUP_STATES['ALREADY_WAIVED']
                rg.save()
    return r


def get_unwaived_rgs(result):
    """
        Return ResultGroups that are not waived (and should be waived)
        for specific Result
    """
    result_waivers = Waiver.objects.filter(result_group__result=result)
    return [rg for rg in ResultGroup.objects.filter(result=result,
            state=RESULT_GROUP_STATES['NEEDS_INSPECTION'])
            if not result_waivers.filter(result_group=rg)]


def compare_result_groups(rg1, rg2):
    """
        Compare defects on two distinct result groups
        This should be as
    """
    if rg1.new_defects != rg2.new_defects:
        return False
    rg1_defects = rg1.get_new_defects()
    rg2_defects = rg2.get_new_defects()

    for rg1_defect in rg1_defects:
        try:
            rg2_defect = rg2_defects.get(checker=rg1_defect.checker)
        except ObjectDoesNotExist:
            return False
        if rg1_defect.checker != rg2_defect.checker:
            return False
        if len(rg1.events) != len(rg2.events):
            return False
    return True


def get_last_waiver(checker_group, package, release):
    """
    Try to get base waiver for specific checkergroup, package, release
    """
    waivers = Waiver.objects.filter(
        result_group__checker_group=checker_group,
        result_group__result__scanbinding__scan__package=package,
        result_group__result__scanbinding__scan__tag__release=release,
    )
    if waivers:
        return waivers.latest()
    else:
        return None