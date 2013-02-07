# -*- coding: utf-8 -*-

import copy
import re
import logging

from django.conf import settings
#from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from covscanhub.scan.models import Scan, SCAN_STATES, SCAN_TYPES, Package, \
    ScanBinding
from covscanhub.scan.service import get_latest_sb_by_package, \
    get_latest_binding
from covscanhub.other.shortcuts import check_brew_build, \
    check_and_create_dirs, get_tag_by_name
from covscanhub.other.exceptions import ScanException

from kobo.hub.models import Task, TASK_STATES

logger = logging.getLogger(__name__)


def create_errata_base_scan(kwargs, parent_task_id, package):
    options = {}

    task_user = kwargs['task_user']
    username = kwargs['username']
    scan_type = SCAN_TYPES['ERRATA_BASE']
    nvr = kwargs['base']
    task_label = nvr
    options['brew_build'] = nvr

    try:
        tag = kwargs['base_tag']
    except KeyError:
        raise RuntimeError("Key 'base_tag' is missing from %s" % kwargs)

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
        args={},  # I want to add scan's id here, so I update it later
        comment=comment,
        state=TASK_STATES["FREE"],
        priority=priority,
        parent_id=parent_task_id,
    )
    task_dir = Task.get_task_dir(task_id)

    check_and_create_dirs(task_dir)

    scan = Scan.create_scan(scan_type=scan_type, nvr=nvr, username=username,
                            tag=tag_obj, package=package, enabled=False)

    options["scan_id"] = scan.id
    # DO NOT USE filter...update() -- invalid json is filled in db
    task = Task.objects.get(id=task_id)
    task.args = options
    task.save()

    sb = ScanBinding()
    sb.task = task
    sb.scan = scan
    sb.save()

    return scan


def obtain_base(base, task_id, kwargs, package):
    binding = get_latest_binding(base)
    found = bool(binding)
    if found:
        if (binding.scan.state == SCAN_STATES['QUEUED'] or
            binding.scan.state == SCAN_STATES['SCANNING']) and \
                binding.result is None:
            return binding.scan
        elif binding.result is None:
            found = False
        elif binding.result.scanner_version != settings.ACTUAL_SCANNER[1] or \
                binding.result.scanner != settings.ACTUAL_SCANNER[0]:
            found = False
    if not found:
        parent_task = Task.objects.get(id=task_id)
        base_obj = create_errata_base_scan(copy.deepcopy(kwargs), task_id,
                                           package)

        # wait has to be after creation of new subtask
        # TODO wait should be executed in one transaction with creation of
        # child
        parent_task.wait()
        return base_obj
    return binding.scan


def check_obsolete_scan(package, release):
    bindings = ScanBinding.objects.filter(
        scan__package=package,
        scan__tag__release=release,
        scan__scan_type=SCAN_TYPES['ERRATA'])
    for binding in bindings:
        if (binding.scan.state == SCAN_STATES['QUEUED'] or
                binding.scan.state == SCAN_STATES['BASE_SCANNING']):
            binding.task.cancel_task(recursive=False)
            Scan.objects.filter(id=binding.scan.id).update(
                state=SCAN_STATES['CANCELED'],
                enabled=False,
            )


def check_package_eligibility(package, created):
    if created:
        logger.warn('Package %s was created', package)
    if not created and package.blocked:
        raise RuntimeError('Package %s is blacklisted' % (package.name))
    elif not created and not package.eligible:
        raise RuntimeError('Package %s is not able to be scanned' %
                           (package.name))


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

    return scanbinding
    """
    options = {}

    #from request.user
    task_user = kwargs['task_user']

    scan_type = kwargs['scan_type']

    #supplied by scan initiator
    try:
        username = kwargs['username']
    except KeyError:
        raise RuntimeError("Key 'username' is missing from %s" % kwargs)

    try:
        nvr = kwargs['nvr']
    except KeyError:
        raise RuntimeError("Key 'nvr' is missing from %s" % kwargs)

    try:
        base = kwargs['base']
    except KeyError:
        raise RuntimeError("Key 'base' is missing from %s" % kwargs)

    try:
        options['errata_id'] = kwargs['id']
    except KeyError:
        raise RuntimeError("Key 'id' is missing from %s" % kwargs)

    options['brew_build'] = nvr

    #Label, description or any reason for this task.
    task_label = nvr

    try:
        tag = kwargs['nvr_tag']
    except KeyError:
        raise RuntimeError("Key 'nvr_tag' is missing from %s" % kwargs)

    priority = kwargs.get('priority', settings.ET_SCAN_PRIORITY)

    comment = 'Errata Tool Scan of %s' % nvr

    #does tag exist?
    tag_obj = get_tag_by_name(tag)
    options['mock_config'] = tag_obj.mock.name

    # Test if build exists
    # TODO: add check if SRPM exist:
    #    GET /brewroot/.../package/version-release/...src.rpm
    check_brew_build(nvr)

    # validation of nvr, creating appropriate package object
    pattern = '(.*)-(.*)-(.*)'
    m = re.match(pattern, nvr)
    if m is not None:
        package_name = m.group(1)
        package, created = Package.objects.get_or_create(name=package_name)
        check_package_eligibility(package, created)
    else:
        raise RuntimeError('%s is not a correct N-V-R (does not match "%s"\
)' % (nvr, pattern))

    check_obsolete_scan(package, tag_obj.release)

    task_id = Task.create_task(
        owner_name=task_user,
        label=task_label,
        method='ErrataDiffBuild',
        args={},  # I want to add scan's id here, so I update it later
        comment=comment,
        state=TASK_STATES["FREE"],
        priority=priority,
    )
    task_dir = Task.get_task_dir(task_id)

    check_and_create_dirs(task_dir)

    # if base is specified, try to fetch it; if it doesn't exist, create
    # new scan for it
    base_obj = obtain_base(base, task_id, kwargs, package)

    child = get_latest_sb_by_package(tag_obj, package)

    scan = Scan.create_scan(scan_type=scan_type, nvr=nvr, username=username,
                            tag=tag_obj, package=package, base=base_obj,
                            enabled=True)

    if base_obj.state != SCAN_STATES['FINISHED']:
        scan.state = SCAN_STATES['BASE_SCANNING']
        scan.save()

    if child and child.scan:
        child_scan = Scan.objects.get(id=child.scan.id)
        child_scan.parent = scan
        child_scan.enabled = False
        child_scan.save()

    options['scan_id'] = scan.id
    task = Task.objects.get(id=task_id)
    task.args = options
    task.save()

    sb = ScanBinding()
    sb.task = task
    sb.scan = scan
    sb.save()

    return sb


def rescan(scan):
    latest_binding = get_latest_binding(scan.nvr)

    if latest_binding.scan.state != SCAN_STATES['FAILED']:
        raise ScanException("You are trying to rescan a scan that haven't \
failed. This is not supported.")

    #scan is base scan
    if scan.is_errata_base_scan() or (Scan.objects.filter(base=scan)):
        task_id = Task.create_task(
            owner_name=latest_binding.task.owner.username,
            label=latest_binding.task.label,
            method='ErrataDiffBuild',
            args={},
            comment=latest_binding.task.comment,
            state=TASK_STATES["FREE"],
            priority=latest_binding.task.priority,
        )
        task_dir = Task.get_task_dir(task_id)

        check_and_create_dirs(task_dir)

        scan = Scan.create_scan(
            scan_type=latest_binding.scan.scan_type,
            nvr=latest_binding.scan.nvr,
            username=latest_binding.scan.username.username,
            tag=latest_binding.scan.tag,
            package=latest_binding.scan.package,
            enabled=False)

        options = latest_binding.task.args
        options.update({'scan_id': scan.id})
        task = Task.objects.get(id=task_id)
        task.args = options
        task.save()

        sb = ScanBinding()
        sb.task = task
        sb.scan = scan
        sb.save()
    #scan is errata scan
    # do not forget to set up parent id for task
    else:
        if latest_binding.task.parent:
            raise ScanException('You want to rescan a scan that has a parent. \
Unsupported.')
        task_id = Task.create_task(
            owner_name=latest_binding.task.owner.username,
            label=latest_binding.task.label,
            method='ErrataDiffBuild',
            args={},
            comment=latest_binding.task.comment,
            state=TASK_STATES["FREE"],
            priority=latest_binding.task.priority,
        )
        task_dir = Task.get_task_dir(task_id)

        check_and_create_dirs(task_dir)

        child = scan.get_child_scan()

        scan = Scan.create_scan(
            scan_type=latest_binding.scan.scan_type,
            nvr=latest_binding.scan.nvr,
            username=latest_binding.scan.username.username,
            tag=latest_binding.scan.tag,
            package=latest_binding.scan.package,
            enabled=True,
            base=get_latest_binding(scan.base.nvr).scan)

        if child:
            child.parent = scan
            child.save()

        options = latest_binding.task.args
        options.update({'scan_id': scan.id})
        task = Task.objects.get(id=task_id)
        task.args = options
        task.save()

        sb = ScanBinding()
        sb.task = task
        sb.scan = scan
        sb.save()