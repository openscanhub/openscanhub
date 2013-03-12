# -*- coding: utf-8 -*-

import re
import logging
from utils import depend_on, spawn_scan_task, _spawn_scan_task
from django.conf import settings
from kobo.rpmlib import parse_nvr
#from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from covscanhub.scan.models import Scan, SCAN_STATES, SCAN_TYPES, Package, \
    ScanBinding, MockConfig, ReleaseMapping, ETMapping, SCAN_STATES_IN_PROGRESS
from covscanhub.scan.xmlrpc_helper import cancel_scan
from covscanhub.other.shortcuts import check_brew_build, \
    check_and_create_dirs
from covscanhub.other.exceptions import ScanException
from covscanhub.scan.service import get_latest_sb_by_package, \
    get_latest_binding

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
        (d['target'], kwargs['target'])

    # Test if SRPM exists
    check_brew_build(d['target'])

    mock_name = assign_mock_config(re.match(".+-.+-(.+)",
                                            d['target']).group(1))
    if mock_name:
        options['mock_config'] = mock_name
    else:
        logger.error("Unable to assign mock profile to base scan %s of \
%s", d['target'], kwargs['target'])
        raise RuntimeError("Unable to assign mock profile to base scan %s of \
%s" % (d['target'], kwargs['target']))

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
        scan__scan_type=SCAN_TYPES['ERRATA'])
    for binding in bindings:
        if binding.scan.state in SCAN_STATES_IN_PROGRESS:
            cancel_scan(binding.scan.id)


def check_package_eligibility(package, nvr, created):
    if created:
        logger.warn('Package %s was created', package)

        depends_on = depend_on(nvr, 'libc.so')
        package.eligible = depends_on
        package.save()

    if not created and package.blocked:
        raise RuntimeError('Package %s is blacklisted' % (package.name))
    elif not package.eligible:
        raise RuntimeError('Package %s is not eligible for scanning' %
                           (package.name))


def assign_mock_config(dist_tag):
    """
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
    raise RuntimeError("This package is not suitable for scanning.")


def return_or_raise(key, data):
    """Custom function for retrieving data from dict (mainly for logging)"""
    try:
        return data[key]
    except KeyError:
        logger.error("Key '%s' is missing from dict '%s'", key, data)
        raise RuntimeError("Key '%s' is missing from %s, invalid scan \
submission!" % (key, data))


def create_errata_scan(kwargs):
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

    try:
        target_nvre_dict = parse_nvr(kwargs['target'])
    except ValueError:
        logger.error('%s is not a correct N-V-R', kwargs['target'])
        raise RuntimeError('%s is not a correct N-V-R' % kwargs['target'])

    etm = ETMapping()
    # ET internal id for the scan record in ET
    etm.et_scan_id = return_or_raise('id', kwargs)
    # ET internal id of the advisory that the build is part of
    etm.advisory_id = return_or_raise('errata_id', kwargs)
    etm.save()

    # one of RHEL-6.2.0, RHEL-6.2.z, etc.
    rhel_version = return_or_raise('rhel_version', kwargs)
    # The advisory's release (mainly for knowledge of advisory being 'ASYNC')
    # values: RHEL-6.2.0, RHEL-6.2.z, ASYNC
    release = return_or_raise('release', kwargs)

    options['brew_build'] = kwargs['target']

    #Label, description or any reason for this task.
    d['task_label'] = kwargs['target']

    d.setdefault('priority', settings.ET_SCAN_PRIORITY)
    d['comment'] = 'Errata Tool Scan of %s' % kwargs['target']

    # Test if build exists
    # TODO: add check if SRPM exist:
    #    GET /brewroot/.../package/version-release/...src.rpm
    check_brew_build(kwargs['target'])

    # validation of nvr, creating appropriate package object
    package, created = Package.objects.get_or_create(
        name=target_nvre_dict['name'])
    check_package_eligibility(package, kwargs['target'], created)
    d['package'] = package

    # returns (mock config's name, tag object)
    tag = get_tag(release)
    if tag:
        options['mock_config'] = tag.mock.name
    else:
        raise RuntimeError("Unable to assign mock profile.")
    check_obsolete_scan(package, tag.release)
    d['tag'] = tag

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

    return etm


def rescan(scan, user):
    """
        Rescan supplied scan.

        @param scan - scan to be rescanned
        @type scan - covscanhub.scan.models.Scan
        @param user - user that triggered resubmit
        @type scan - django...User
    """
    latest_binding = get_latest_binding(scan.nvr, show_failed=True)
    logger.info('Rescheduling scan with nvr %s, latest binding %s',
                scan.nvr, latest_binding)

    if latest_binding.scan.state != SCAN_STATES['FAILED']:
        raise ScanException("Latest run of %s haven't \
failed. This is not supported." % scan.nvr)

    #scan is base scan
    if latest_binding.scan.is_errata_base_scan():
        task_id = latest_binding.task.clone_task(
            user,
            state=TASK_STATES["CREATED"],
            args={},
            comment="Rescan of base %s" % latest_binding.scan.nvr,
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
        options.update({'scan_id': scan.id})
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
