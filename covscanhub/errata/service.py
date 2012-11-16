# -*- coding: utf-8 -*-

import copy
import re

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from covscanhub.scan.models import Scan, SCAN_STATES, SCAN_TYPES, Package
from covscanhub.scan.service import get_latest_scan_by_package
from covscanhub.other.shortcuts import check_brew_build, \
    check_and_create_dirs, get_tag_by_name
from kobo.hub.models import Task


def create_errata_base_scan(kwargs, task_id, package):
    options = {}

    task_user = kwargs['task_user']
    username = kwargs['username']
    scan_type = SCAN_TYPES['ERRATA_BASE']
    base_obj = None
    nvr = kwargs['base']
    task_label = nvr
    options['brew_build'] = nvr

    tag = kwargs['base_tag']

    priority = kwargs.get('priority', settings.ET_SCAN_PRIORITY) + 1
    comment = 'Errata Tool Base scan of %s requested by %s' % \
        (nvr, kwargs['nvr'])

    # Test if SRPM exists
    check_brew_build(nvr)

    #does tag exist?
    tag_obj = get_tag_by_name(tag)
    options['mock_config'] = tag_obj.mock.name

    task_id = Task.create_task(
        owner_name=task_user,
        label=task_label,
        method='ErrataDiffBuild',
        args={}, # I want to add scan's id here, so I update it later
        comment=comment,
        state=SCAN_STATES["QUEUED"],
        priority=priority,
        parent_id=task_id,
    )
    task_dir = Task.get_task_dir(task_id)

    check_and_create_dirs(task_dir)

    # if base is specified, try to fetch it; if it doesn't exist, create
    # new task for it
    scan = Scan.create_scan(scan_type=scan_type, nvr=nvr, task_id=task_id,
                            tag=tag_obj, package=package, base=base_obj,
                            username=username)
    scan.save()

    options['scan_id'] = scan.id
    task = Task.objects.get(id=task_id)
    task.args = options
    task.save()

    return scan


def create_errata_scan(kwargs):
    """
    create scan of a package and perform diff on results against specified
    version
    options of this scan are in dict 'kwargs'

    kwargs
     - scan_type - type of scan (SCAN_TYPES in covscanhub.scan.models)
     - username - name of user who is requesting scan (from ET)
     - task_user - username from request.user.username
     - nvr - name, version, release of scanned package
     - base - previous version of package, the one to make diff against
     - id - errata ID
     - nvr_tag - tag of the package from brew
     - base_tag - tag of the base package from brew
     - rhel_version - version of enterprise linux in which will package appear
    """
    options = {}

    #from request.user
    task_user = kwargs['task_user']

    #supplied by scan initiator
    username = kwargs['username']
    scan_type = kwargs['scan_type']
    nvr = kwargs['nvr']
    base = kwargs['base']
    options['errata_id'] = kwargs['id']
    options['brew_build'] = nvr

    #Label, description or any reason for this task.
    task_label = nvr

    tag = kwargs['nvr_tag']
    priority = kwargs.get('priority', settings.ET_SCAN_PRIORITY)

    #if kwargs does not have 'id', it is base scan
    comment = 'Errata Tool Scan of %s' % nvr

    #does tag exist?
    tag_obj = get_tag_by_name(tag)
    options['mock_config'] = tag_obj.mock.name

    # Test if build exists
    # TODO: add check if SRPM exist:
    #    GET /brewroot/.../package/version-release/...src.rpm
    check_brew_build(nvr)

    task_id = Task.create_task(
        owner_name=task_user,
        label=task_label,
        method='ErrataDiffBuild',
        args={},  # I want to add scan's id here, so I update it later
        comment=comment,
        state=SCAN_STATES["QUEUED"],
        priority=priority,
    )
    task_dir = Task.get_task_dir(task_id)

    check_and_create_dirs(task_dir)

    # validation of nvr, creating appropriate package object
    pattern = '(.*)-(.*)-(.*)'
    m = re.match(pattern, nvr)
    if m is not None:
        package_name = m.group(1)
        package, created = Package.objects.get_or_create(name=package_name)
    else:
        raise RuntimeError('%s is not a correct N-V-R (does not match "%s"\
)' % (nvr, pattern))

    # if base is specified, try to fetch it; if it doesn't exist, create
    # new scan for it
    base_obj = None
    if base:
        try:
            base_obj = Scan.objects.get(nvr=base)
        except ObjectDoesNotExist:
            parent_task = Task.objects.get(id=task_id)
            base_obj = create_errata_base_scan(copy.deepcopy(kwargs), task_id,
                                               package)

            # wait has to be after creation of new subtask
            # TODO wait should be executed in one transaction with creation of
            # child
            parent_task.wait()
        except MultipleObjectsReturned:
            #return latest, but this shouldnt happened
            base_obj = Scan.objects.filter(nvr=base).\
                order_by('-task__dt_finished')[0]

    child = get_latest_scan_by_package(tag_obj, package)

    scan = Scan.create_scan(scan_type=scan_type, nvr=nvr, task_id=task_id,
                            tag=tag_obj, package=package, base=base_obj,
                            username=username)

    if child is not None:
        child.parent = scan
        child.enabled = False
        child.save()

    options['scan_id'] = scan.id
    task = Task.objects.get(id=task_id)
    task.args = options
    task.save()

    return scan