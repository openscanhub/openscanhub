# -*- coding: utf-8 -*-

"""
module for loading defects from JSON formatted files and making operations upon these data
"""

import logging

from kobo.hub.models import Task

from osh.common.csmock_parser import CsmockAPI
from covscanhub.service.path import TaskResultPaths

logger = logging.getLogger(__name__)


def load_file_content(file_path):
    try:
        with open(file_path, 'r') as fd:
            content = fd.read()
    except IOError:
        logger.critical('Unable to open file %s', file_path)
        return
    return content


def load_defects(task_id, with_diff=True, with_results_summary=False):
    """
    Load defects for provided task
    """
    task = Task.objects.get(id=task_id)
    paths = TaskResultPaths(task)

    result = {}
    result['defects'] = CsmockAPI(paths.get_json_results()).get_defects()
    if with_diff:
        result['added'] = CsmockAPI(paths.get_json_added()).get_defects()
        result['fixed'] = CsmockAPI(paths.get_json_fixed()).get_defects()
    if with_results_summary:
        result['results_summary'] = load_file_content(paths.get_txt_summary())
    return result


def get_defect_stats(defects):
    """
    create dict with stats for provided list of defects:
    {
        'defect_type': count,
    }
    """
    result = {}
    if defects:
        for defect in defects:
            result.setdefault(defect['checker'], 0)
            result[defect['checker']] += 1
    return result
