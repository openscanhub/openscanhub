# -*- coding: utf-8 -*-

"""
module for loading defects from JSON formatted files and making operations upon these data
"""

import os
import json
import logging

from kobo.hub.models import Task
from covscanhub.other.constants import SCAN_RESULTS_FILENAME, FIXED_DIFF_FILE, \
    ERROR_DIFF_FILE, DEFECTS_IN_PATCHES_FILE


logger = logging.getLogger(__name__)


def load_defects_from_json(json_dict):
    """
    return list of defects from provided json dict
    """
    if 'defects' in json_dict:
        return json_dict['defects']
    else:
        return []


def load_defects_from_file(file_path):
    try:
        fd = open(file_path, 'r')
    except IOError:
        logger.critical('Unable to open file %s', file_path)
        return
    js = json.load(fd)
    defects = load_defects_from_json(js)
    fd.close()
    return defects


def load_defects(task_id, with_diff=True, with_defects_in_patches=False):
    """
    Load defects for provided task
    """
    task = Task.objects.get(id=task_id)
    task_dir = task.task_dir()
    dir_name = task.label
    if dir_name.endswith('.src.rpm'):
        dir_name = dir_name[:-8]
    defects_path = os.path.join(task_dir, dir_name, 'run1', SCAN_RESULTS_FILENAME)
    if with_diff:
        fixed_file_path = os.path.join(task_dir, FIXED_DIFF_FILE)
        added_file_path = os.path.join(task_dir, ERROR_DIFF_FILE)
    result = {}
    result['defects'] = load_defects_from_file(defects_path)
    if with_diff:
        result['added'] = load_defects_from_file(added_file_path)
        result['fixed'] = load_defects_from_file(fixed_file_path)
    if with_defects_in_patches:
        dip_path = os.path.join(task_dir, dir_name, DEFECTS_IN_PATCHES_FILE)
        result['defects_in_patches'] = load_defects_from_file(dip_path)
    return result


def get_defect_stats(defects):
    """
    create dict with stats for provided list of defects:
    {
        'defect_type': count,
    }
    """
    result = {}
    for defect in defects:
        result.setdefault(defect['checker'], 0)
        result[defect['checker']] += 1
    return result