# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import logging
import os
import shutil

import kobo.hub.xmlrpc.worker as kobo_xmlrpc_worker
from django.conf import settings
from kobo.client.constants import TASK_STATES
from kobo.django.upload.models import FileUpload
from kobo.hub.decorators import validate_worker
from kobo.hub.models import Task
from kobo.hub.xmlrpc.worker import open_task as kobo_open_task

from osh.hub.scan.mock import generate_mock_configs
from osh.hub.scan.models import (SCAN_STATES, AnalyzerVersion, AppSettings,
                                 Profile, Scan, ScanBinding)
from osh.hub.scan.notify import send_task_notification
from osh.hub.scan.scanner import (move_mock_configs, obtain_base,
                                  prepare_base_scan)
from osh.hub.scan.xmlrpc_helper import cancel_scan
from osh.hub.scan.xmlrpc_helper import fail_scan as h_fail_scan
from osh.hub.scan.xmlrpc_helper import finish_scan as h_finish_scan
from osh.hub.scan.xmlrpc_helper import (prepare_version_retriever,
                                        scan_notification_email)
from osh.hub.service.csmock_parser import unpack_and_return_api
from osh.hub.waiving.results_loader import TaskResultsProcessor

logger = logging.getLogger(__name__)

# DO NOT REMOVE!  The __all__ list contains all publicly exported XML-RPC
# methods from this module.
__all__ = [
    'create_mock_configs',
    'cancel_task',
    'create_sb',
    'email_scan_notification',
    'email_task_notification',
    'ensure_base_is_scanned_properly',
    'ensure_cache',
    'fail_scan',
    'fail_task',
    'finish_analyzers_version_retrieval',
    'finish_scan',
    'finish_task',
    'get_scanning_args',
    'get_su_user',
    'interrupt_tasks',
    'move_upload',
    'open_task',
    'set_scan_to_basescanning',
    'set_scan_to_scanning',
]


# REGULAR TASKS

# FIXME: The configs should be created before the subtask is scheduled!
@validate_worker
def create_mock_configs(request, task_id):
    task = Task.objects.get(id=task_id)
    task_dir = Task.get_task_dir(task_id, create=True)

    # skip if not a subtask
    if task.parent_id is None:
        return

    # FIXME: Yuck!  Remove when ET tasks use the unified argument format
    if task.method == 'ErrataDiffBuild':
        nvr = task.args['build']
        koji_profile = Profile.objects.get(name=task.args['profile']).command_arguments.get('koji_profile', 'koji')
    else:
        nvr = task.args['build']['nvr']
        koji_profile = task.args['build']['koji_profile']

    tmpdir = generate_mock_configs(nvr, koji_profile)
    move_mock_configs(tmpdir, task_dir)


@validate_worker
def email_task_notification(request, task_id):
    try:
        logger.debug('email_task_notification for %s', task_id)
        return send_task_notification(request, task_id)
    finally:
        if settings.ENABLE_SINGLE_USE_WORKERS:
            task = Task.objects.get(id=task_id)
            logger.debug('Disable worker %s', task.worker.name)
            task.worker.enabled = False
            task.worker.save()


@validate_worker
def finish_task(request, task_id):
    logger.info("Finishing task %s", task_id)
    task = Task.objects.get(id=task_id)
    base_task = None
    if task.subtasks():
        base_task = task.subtasks()[0]
    exclude_dirs = AppSettings.settings_get_results_tb_exclude_dirs()
    td = TaskResultsProcessor(task, base_task, exclude_dirs)
    td.unpack_results()
    if base_task:
        try:
            return td.generate_diffs()
        except RuntimeError as ex:
            logger.error("Can't diff tasks %s %s: %s", base_task, task, ex)
            if not task.is_failed():
                task.fail_task()


@validate_worker
def open_task(request, task_id):
    response = kobo_open_task(request, task_id)

    if settings.ENABLE_SINGLE_USE_WORKERS:
        task = Task.objects.get(id=task_id)

        # TODO: Check if we should create shutdown tasks before deleting a worker.
        # This would spam the tasks view with `ShutdownWorker` tasks.
        # It would also require changes in `osh-worker-manager --workers-needed` command.
        # if task.parent is not None:
        #     Task.create_shutdown_task("worker/" + task.worker.name, task.worker.name, kill=False)

        # `VersionDiffBuild` tasks have a subtask (base scan) that is run before the task.
        # Subtasks have `task.parent` field set.
        # If `max_load` is set to 0, when `VersionDiffBuild` moves to open state,
        # base scan would get assigned but never start as `max_load` has been set to 0.
        # Only set `max_load` to 0 when subtask has moved to open state.
        if task.method != "VersionDiffBuild" or task.parent is not None:
            # TODO: This condition would not execute if the subtask fails to reach `open` state.
            # That would cause the main task to fail.
            # And the worker would pick up another task, so it would not be a single use worker.
            # Check if we can workaround such situation by overriding `assign_task` method.
            # Look for `task_count > 0` condition there.

            # Set the worker load to 0. This should avoid getting any new tasks assigned to the worker.
            # Each single use worker should be destroyed once a task completes.
            task.worker.max_load = 0
            task.worker.save()

    return response


# ET SCANS

@validate_worker
def email_scan_notification(request, scan_id):
    try:
        logger.debug('email_scan_notification for %s', scan_id)
        scan_notification_email(request, scan_id)
    finally:
        if settings.ENABLE_SINGLE_USE_WORKERS:
            task = ScanBinding.objects.get(scan__id=scan_id).task
            logger.debug('Disable worker %s', task.worker.name)
            task.worker.enabled = False
            task.worker.save()


@validate_worker
def finish_scan(request, scan_id, filename):
    h_finish_scan(request, scan_id, filename)


@validate_worker
def finish_analyzers_version_retrieval(request, task_id, filename):
    task = Task.objects.get(id=task_id)
    task_dir = Task.get_task_dir(task_id)
    tb_path = os.path.join(task_dir, filename)
    csmock = unpack_and_return_api(tb_path, task_dir)
    if csmock:
        analyzers = csmock.get_analyzers()
        mock_config = task.args['mock_config']
        AnalyzerVersion.objects.update_analyzers_versions(analyzers, mock_config)
    else:
        logger.error("Can't process results of task %s", task)
        if not task.is_failed():
            task.fail_task()


@validate_worker
def get_su_user(request):
    return AppSettings.setting_get_su_user()


@validate_worker
def set_scan_to_basescanning(request, scan_id):
    scan = Scan.objects.get(id=scan_id)
    scan.set_state_basescanning()


@validate_worker
def set_scan_to_scanning(request, scan_id):
    scan = Scan.objects.get(id=scan_id)
    scan.set_state_scanning()


@validate_worker
def fail_scan(request, scan_id, reason=None):
    h_fail_scan(scan_id, reason)


@validate_worker
def get_scanning_args(request, profile):
    return Profile.objects.get(name=profile).command_arguments


@validate_worker
def move_upload(request, task_id, upload_id):
    """ child task's srpm is uploaded, move it to task's dir """
    task_dir = Task.get_task_dir(task_id, create=True)
    upload = FileUpload.objects.get(id=upload_id)
    shutil.move(os.path.join(upload.target_dir, upload.name), os.path.join(task_dir, upload.name))
    upload.delete()


@validate_worker
def create_sb(request, task_id):
    task = Task.objects.get(id=task_id)
    scan = Scan.objects.get(id=task.args['scan_id'])
    ScanBinding.create_sb(task=task, scan=scan)


@validate_worker
def ensure_cache(request, mock_config, profile):
    """
    make sure that cache with version of analyzers is not stale
    """
    if mock_config == 'rhel-9-beta-x86_64':
        # FIXME: hard-coded at two places for now
        mock_config = 'rhel-9-alpha-x86_64'
    if not AnalyzerVersion.objects.is_cache_uptodate(mock_config):
        profile = Profile.objects.get(name=profile)
        analyzers = profile.analyzers
        csmock_args = profile.csmock_args
        su_user = AppSettings.setting_get_su_user()
        return prepare_version_retriever(mock_config, analyzers, su_user, csmock_args)


@validate_worker
def ensure_base_is_scanned_properly(request, scan_id, task_id):
    """
    Make sure that base is scanned properly (with up-to-date analyzers)
    if not, do it (by spawning subtask)

    return (method, args, label)
    """
    scan = Scan.objects.get(id=scan_id)
    if not scan.can_have_base():
        logger.info('Scan %s does not need base', scan)
        return

    task = Task.objects.get(id=task_id)
    base_nvr = task.args['base_nvr']
    mock_config = scan.tag.mock.name
    if mock_config == 'rhel-9-beta-x86_64':
        # FIXME: hard-coded at two places for now
        mock_config = 'rhel-9-alpha-x86_64'

    # Inherit `auto` mock config if parent used it
    if task.args['mock_config'] == 'auto':
        mock_config = 'auto'
        base_scan = None
    else:
        logger.debug("Looking for base scan '%s', mock_config: %s", base_nvr, mock_config)
        base_scan = obtain_base(base_nvr, mock_config)

    if base_scan is None:
        logger.info("Preparing base scan")
        options = {
            'mock_config': mock_config,
            'target': base_nvr,
            'package': scan.package,
            'tag': scan.tag,
            'package_owner': scan.username.username,
            'parent_scan': scan,
            'method': task.method,
        }
        base_task_args = prepare_base_scan(options)
        return base_task_args

    logger.info("Using cached base scan '%s'", base_scan)
    scan.set_base(base_scan)


@validate_worker
def cancel_task(request, task_id):
    response = kobo_xmlrpc_worker.cancel_task(request, task_id)

    # cancel the corresponding scan
    sb = ScanBinding.objects.filter(task=task_id).first()
    if sb is not None:
        cancel_scan(sb)

    return response


@validate_worker
def fail_task(request, task_id, task_result):
    response = kobo_xmlrpc_worker.fail_task(request, task_id, task_result)

    # fail the corresponding scan
    sb = ScanBinding.objects.filter(task=task_id).first()
    if sb is not None and sb.scan.state != SCAN_STATES['FAILED']:
        fail_scan(request, sb.scan.id, 'Unspecified failure')

    return response


@validate_worker
def interrupt_tasks(request, task_list):
    response = kobo_xmlrpc_worker.interrupt_tasks(request, task_list)

    for task_id in task_list:
        task = Task.objects.get(id=task_id)
        if task.state != TASK_STATES["INTERRUPTED"]:
            continue

        sb = ScanBinding.objects.filter(task=task).first()
        if sb is None:
            continue

        fail_scan(request, sb.scan.id, 'Task was interrupted')

    return response
