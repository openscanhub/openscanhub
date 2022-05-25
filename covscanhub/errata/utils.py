# -*- coding: utf-8 -*-

import re
import koji
import logging

from kobo.rpmlib import parse_nvr
from kobo.hub.models import Task, TASK_STATES

from covscanhub.scan.models import SCAN_TYPES, Scan
from covscanhub.other.shortcuts import check_and_create_dirs

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import six

__all__ = (
    "spawn_scan_task",
    "_spawn_scan_task",
)

if __name__ == '__main__':
    logger = logging.getLogger('covscanhub.errata.utils')
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)
else:
    logger = logging.getLogger(__name__)

s = koji.ClientSession(settings.BREW_URL)


def get_or_fail(key, data):
    """ Convenience function for retrieving data from dict """
    try:
        return data[key]
    except KeyError:
        logger.error("Key '%s' is missing from dict '%s'", key, data)
        raise RuntimeError("Key '%s' is missing from '%s'!" % (key, data))


def _spawn_scan_task(d):
    """
    parent method that actually creates Task and Scan

    @type d: dict
    """
    task_id = Task.create_task(
        owner_name=d['task_user'],
        label=d['task_label'],
        method=d['method'],
        args={},  # I want to add scan's id here, so I update it later
        comment=d['comment'],
        state=TASK_STATES["CREATED"],
        priority=d['priority'],
        parent_id=d.get('parent_id', None),
    )
    task_dir = Task.get_task_dir(task_id)

    check_and_create_dirs(task_dir)

    scan = Scan.create_scan(scan_type=d['scan_type'], nvr=d['target'],
                            username=d['package_owner'],
                            tag=d['tag'], package=d['package'],
                            enabled=d['scan_enabled'])
    return task_id, scan

##########
# SPAWNING
##########


def spawn_newpkg(d):
    d.update((
        ('method', 'ErrataDiffBuild'),
        ('scan_type', SCAN_TYPES['NEWPKG']),
    ), )
    return _spawn_scan_task(d)


def spawn_rebase(d):
    d.update((
        ('method', 'ErrataDiffBuild'),
        ('scan_type', SCAN_TYPES['REBASE']),
    ), )
    return _spawn_scan_task(d)


def spawn_classic(d):
    d.update((
        ('method', 'ErrataDiffBuild'),
        ('scan_type', SCAN_TYPES['ERRATA']),
    ), )
    return _spawn_scan_task(d)


def is_rebase(base, target):
    """ base, target -- NVRs """
    base_d = parse_nvr(base)
    target_d = parse_nvr(target)
    return target_d['version'] != base_d['version']


def spawn_scan_task(d, target):
    """
    Figure out scan type and create scan and task models
    Exported method

    @type d: dict
    @type target: dict (save one parse_nvr call)
    """
    d['scan_enabled'] = True
    if d['base'].lower() == 'new_package':
        return spawn_newpkg(d)
    elif is_rebase(d['base'], target):
        return spawn_rebase(d)
    else:
        return spawn_classic(d)
