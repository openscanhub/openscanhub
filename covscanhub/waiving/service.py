# -*- coding: utf-8 -*-

"""
    compilation of functions that provide functionality for waiving and fill
    database with defects from scan
"""

import os
import re
import logging

import django.utils.simplejson as json
from django.core.exceptions import ObjectDoesNotExist

from covscanhub.other.constants import ERROR_DIFF_FILE, FIXED_DIFF_FILE
from models import DEFECT_STATES, Defect, Event, Result, \
    Checker, CheckerGroup, Waiver

from kobo.hub.models import Task


logger = logging.getLogger(__name__)


__all__ = (
    'create_results',
    'get_groups_by_result',
    'get_waiving_status',
    'get_missing_waivers',
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
                checker = Checker.objects.get(name=json_checker_name)
            except ObjectDoesNotExist:
                checker = Checker()
                checker.name = json_checker_name
                checker.group = CheckerGroup.objects.get(name='Default')
                checker.save()
            d.checker = checker
            d.annotation = defect.get('annotation', None)
            d.defect_identifier = defect.get('defect_id', None)
            d.function = defect.get('function', None)
            d.result = result
            d.state = defect_state
            d.save()
            # we have to aquire id for 'd' so it is correctly linked to events
            key_event = defect['key_event_idx']

            if 'events' in defect:
                e_id = None
                for event in defect['events']:
                    e = Event()
                    e.file_name = event['file_name']
                    e.line = event['line']
                    e.column = event.get('column', None)
                    e.event = event['event']
                    e.message = event['message']
                    e.defect = d
                    e.save()
                    if e_id is None:
                        if key_event == 0:
                            e_id = e
                        else:
                            key_event -= 1
                #e_id could be None
                d.key_event = e_id
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
                result.scanner_version = version
    result.save()


def create_results(scan):
    """
    Task finished, so this method should update results
    """
    logger.debug('Creating results for scan %s', scan)
    task_dir = Task.get_task_dir(scan.task.id)

    #json's path is <TASK_DIR>/<NVR>/run1/<NVR>.js
    defects_path = os.path.join(task_dir, scan.nvr, 'run1', scan.nvr + '.js')
    fixed_file_path = os.path.join(task_dir, FIXED_DIFF_FILE)
    diff_file_path = os.path.join(task_dir, ERROR_DIFF_FILE)

    try:
        f = open(defects_path, 'r')
    except IOError:
        print 'Unable to open file %s' % defects_path
        return
    json_dict = json.load(f)

    r = Result()

    update_analyzer(r, json_dict)

    r.scan = scan
    r.save()

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
    return r


def get_groups_by_result(result):
    groups = set()

    #filter only newly added bugs
    for defect in Defect.objects.filter(result=result):
        groups.add(defect.checker.group)

    return groups


def get_waiving_status(result):
    result_waivers = Waiver.objects.filter(result=result)
    status = {}
    for group in get_groups_by_result(result):
        status[group] = result_waivers.filter(group=group)
    return status


def get_missing_waivers(result):
    return [group for group, query in get_waiving_status(result).iteritems()
            if not query]