# -*- coding: utf-8 -*-

import logging

import re
from django.conf import settings

from covscanhub.errata.check import check_nvr, check_package_eligibility
from covscanhub.errata.utils import spawn_scan_task, _spawn_scan_task


#from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from covscanhub.scan.models import Scan, SCAN_STATES, SCAN_TYPES, Package, \
    ScanBinding, MockConfig, ReleaseMapping, ETMapping, \
    SCAN_STATES_IN_PROGRESS, AppSettings, SCAN_TYPES_TARGET
from covscanhub.scan.xmlrpc_helper import cancel_scan
from covscanhub.other.shortcuts import check_brew_build, \
    check_and_create_dirs
from covscanhub.other.exceptions import ScanException
from covscanhub.scan.service import get_latest_sb_by_package, \
    get_latest_binding
from covscanhub.service.processing import task_has_newstyle_results

from kobo.hub.models import Task, TASK_STATES

logger = logging.getLogger(__name__)

######
# BASE
######


def create_errata_base_scan(d, parent_task_id):
    """Create base scan according to dict kwargs"""
    options = {}

    d['scan_type'] = SCAN_TYPES['ERRATA_BASE']
    # kwargs['target'] = TARGET, d['target'] = BASE
    d['target'] = d['base']
    del d['base']
    # we don't want bases tagged
    d['tag'] = None

    d['task_label'] = d['target']
    options['brew_build'] = d['target']

    d.setdefault('priority', settings.ET_SCAN_PRIORITY + 1)
    d['comment'] = 'Errata Tool Base scan of %s requested by %s' % \
        (d['target'], d['target'])

    # Test if SRPM exists
    check_brew_build(d['target'])

    # set profile to be same as target's
    options['mock_config'] = d['mock_config']

    d['method'] = 'ErrataDiffBuild'
    d['parent_id'] = parent_task_id
    d['scan_enabled'] = False
    task_id, scan = _spawn_scan_task(d)

    options["scan_id"] = scan.id

    # DO NOT USE filter...update() -- invalid json is filled in db
    task = Task.objects.get(id=task_id)
    task.args = options
    task.save()
    task.free_task()

    sb = ScanBinding()
    sb.task = task
    sb.scan = scan
    sb.save()

    return scan


def obtain_base(d, task_id):
    """
    @type task_id - int (parent task ID)
    @type d - dict (dict with scan settings)
    """
    binding = get_latest_binding(d['base'])
    found = bool(binding)
    if found:
        actual_scanner = AppSettings.settings_actual_scanner()
        if (binding.scan.state == SCAN_STATES['QUEUED'] or
            binding.scan.state == SCAN_STATES['SCANNING']) and \
                binding.result is None:
            return binding.scan
        elif binding.result is None:
            found = False
        elif binding.result.scanner_version != actual_scanner[1] or \
                binding.result.scanner != actual_scanner[0]:
            found = False
        elif not task_has_newstyle_results(binding.task):
            found = False
    if not found:
        parent_task = Task.objects.get(id=task_id)
        base_obj = create_errata_base_scan(d, task_id)

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
        scan__scan_type__in=SCAN_TYPES_TARGET)
    for binding in bindings:
        if binding.scan.state in SCAN_STATES_IN_PROGRESS:
            cancel_scan(binding.scan.id)


def assign_mock_config(dist_tag):
    """
        NOT USED:, base scan inherits mock profile from target

        Assign appropriate mock config according to 'dist_tag', if this fails
        fallback to rhel-6 -- there is at least some output
    """
    try:
        release = re.match(".+\.el(\d)", dist_tag).group(1)
        mock = MockConfig.objects.get(name="rhel-%s-x86_64" % release)
    except Exception, ex:
        logger.error("Unable to find proper mock profile for dist_tag %s: %s"
                     % (dist_tag, ex))
        return MockConfig.objects.get(get="rhel-6-x86_64").name
    else:
        return mock.name


def get_tag(release):
    for rm in ReleaseMapping.objects.all():
        tag = rm.get_tag(release)
        if tag:
            return tag
    logger.critical("Unable to assign proper product and release: %s", release)
    raise RuntimeError("Packages in this release are not being scanned.")


def return_or_raise(key, data):
    """Custom function for retrieving data from dict (mainly for logging)"""
    try:
        return data[key]
    except KeyError:
        logger.error("Key '%s' is missing from dict '%s'", key, data)
        raise RuntimeError("Key '%s' is missing from %s, invalid scan \
submission!" % (key, data))


def create_errata_scan(kwargs, etm):
    """
    create scan of a package and perform diff on results against specified
     version
    options of this scan are in dict 'kwargs'

    kwargs
     - package_owner - name of the package for the advisory owner
     - target - name, version, release of scanned package (brew build)
     - base - previous version of package, the one to make diff against
     - id - ET internal id for the scan record in ET
     - errata_id - the ET internal id of the advisory that the build is part of
     - rhel_version - short tag of rhel version -- product (e. g. 'RHEL-6.3.Z')
     - release - The advisory's release ('ASYNC', 'RHEL-.*', 'MRG.*')

    return ETMapping
    """
    # dict stored in Task.args and used by task in worker
    options = {}

    # dict for creation of Scan and Task objects
    d = kwargs.copy()

    # be sure that dict contains all necessary data
    return_or_raise('package_owner', kwargs)
    return_or_raise('target', kwargs)
    return_or_raise('base', kwargs)

    # validation of nvr
    target_nvre_dict = check_nvr(kwargs['target'])

    # first thing, create entry in DB about provided package
    package, created = Package.objects.get_or_create(
        name=target_nvre_dict['name'])

    # The advisory's release (mainly for knowledge of advisory being 'ASYNC')
    # values: RHEL-6.2.0, RHEL-6.2.z, ASYNC
    release = return_or_raise('release', kwargs)
    # returns (mock config's name, tag object)
    tag = get_tag(release)
    if tag:
        options['mock_config'] = tag.mock.name
        d['mock_config'] = tag.mock.name
    else:
        raise RuntimeError("Unable to assign mock profile.")
    check_obsolete_scan(package, tag.release)
    d['tag'] = tag

    # check if package is written in scannable language and is not blacklisted
    check_package_eligibility(package, kwargs['target'],
                              options['mock_config'], tag.release,
                              created)
    d['package'] = package

    ## one of RHEL-6.2.0, RHEL-6.2.z, etc.
    #rhel_version = return_or_raise('rhel_version', kwargs)

    options['brew_build'] = kwargs['target']

    #Label, description or any reason for this task.
    d['task_label'] = kwargs['target']

    d.setdefault('priority', settings.ET_SCAN_PRIORITY)
    d['comment'] = 'Errata Tool Scan of %s' % kwargs['target']

    # Test if build exists
    # TODO: add check if SRPM exist:
    #    GET /brewroot/.../package/version-release/...src.rpm
    check_brew_build(kwargs['target'])

    child = get_latest_sb_by_package(d['tag'].release, d['package'])

    # is it rebase? new pkg? or ordinary scan? spawn appropriate models to DB
    task_id, scan = spawn_scan_task(d, target_nvre_dict)

    if scan.can_have_base():
        base = obtain_base(d.copy(), task_id)
        scan.base = base
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
    task.free_task()

    sb = ScanBinding()
    sb.task = task
    sb.scan = scan
    sb.save()

    etm.latest_run = sb
    etm.save()

    scan.set_state(SCAN_STATES['QUEUED'])


def rescan(scan, user):
    """
        Rescan supplied scan.

        @param scan - scan to be rescanned
        @type scan - covscanhub.scan.models.Scan
        @param user - user that triggered resubmit
        @type user - django...User
    """
    latest_binding = get_latest_binding(scan.nvr, show_failed=True)
    logger.info('Rescheduling scan with nvr %s, latest binding %s',
                scan.nvr, latest_binding)

    if latest_binding.scan.state != SCAN_STATES['FAILED']:
        raise ScanException("Latest run %d of %s haven't \
failed. This is not supported." % (latest_binding.scan.id, scan.nvr))

    #scan is base scan
    if latest_binding.scan.is_errata_base_scan():
        #clone does not support cloning of child tasks only
        task_id = Task.create_task(
            owner_name=latest_binding.task.owner.username,
            label=latest_binding.task.label,
            method=latest_binding.task.method,
            args={},
            comment="Rescan of base %s" % latest_binding.scan.nvr,
            state=TASK_STATES["CREATED"],
            priority=latest_binding.task.priority,
            resubmitted_by=user,
            resubmitted_from=latest_binding.task,
        )

        task_dir = Task.get_task_dir(task_id)

        check_and_create_dirs(task_dir)
        new_scan = latest_binding.scan.clone_scan()

        options = latest_binding.task.args
        options.update({'scan_id': new_scan.id})
        task = Task.objects.get(id=task_id)
        task.args = options
        task.save()
        task.free_task()

        sb = ScanBinding()
        sb.task = task
        sb.scan = new_scan
        sb.save()

        return sb
    # scan is errata scan
    # do not forget to set up parent id for task
    else:
        if latest_binding.task.parent:
            raise ScanException('You want to rescan a scan that has a parent. \
Unsupported.')

        latest_base_binding = get_latest_binding(scan.base.nvr)
        if not latest_base_binding:
            raise RuntimeError('It looks like that any of base scans of %s \
did not finish successfully; reschedule base (latest base: %s)' % (
                scan.base.nvr,
                get_latest_binding(scan.base.nvr, show_failed=True))
            )

        task_id = latest_binding.task.clone_task(
            user,
            state=TASK_STATES["CREATED"],
            args={},
            comment="Rescan of %s" % latest_binding.scan.nvr,
        )

        task_dir = Task.get_task_dir(task_id)

        check_and_create_dirs(task_dir)

        # update child
        child = scan.get_child_scan()

        new_scan = latest_binding.scan.clone_scan(
            base=latest_base_binding.scan)

        if child:
            child.parent = scan
            child.save()

        options = latest_binding.task.args
        options.update({'scan_id': new_scan.id})
        task = Task.objects.get(id=task_id)
        task.args = options
        task.save()
        task.free_task()

        sb = ScanBinding()
        sb.task = task
        sb.scan = new_scan
        sb.save()

        ETMapping.objects.filter(
            latest_run=latest_binding).update(latest_run=sb)

        return sb
