# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import logging
import os
import shutil

import kobo.hub.xmlrpc.worker as kobo_xmlrpc_worker
from kobo.client.constants import TASK_STATES
from kobo.django.upload.models import FileUpload
from kobo.hub.decorators import validate_worker
from kobo.hub.models import Task

from osh.hub.errata.models import ScanningSession
from osh.hub.errata.scanner import (BaseNotValidException, obtain_base,
                                    prepare_base_scan)
from osh.hub.scan.models import (SCAN_STATES, AnalyzerVersion, AppSettings,
                                 Scan, ScanBinding)
from osh.hub.scan.notify import send_task_notification
from osh.hub.scan.xmlrpc_helper import cancel_scan
from osh.hub.scan.xmlrpc_helper import fail_scan as h_fail_scan
from osh.hub.scan.xmlrpc_helper import finish_scan as h_finish_scan
from osh.hub.scan.xmlrpc_helper import (prepare_version_retriever,
                                        scan_notification_email)
from osh.hub.service.csmock_parser import unpack_and_return_api
from osh.hub.waiving.results_loader import TaskResultsProcessor

logger = logging.getLogger(__name__)


# REGULAR TASKS

@validate_worker
def email_task_notification(request, task_id):
    logger.debug('email_task_notification for %s', task_id)
    return send_task_notification(request, task_id)


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


# ET SCANS

@validate_worker
def email_scan_notification(request, scan_id):
    scan_notification_email(request, scan_id)


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
def get_scanning_args(request, scanning_session_id):
    scanning_session = ScanningSession.objects.get(id=scanning_session_id)
    return scanning_session.profile.command_arguments


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
def ensure_cache(request, mock_config, scanning_session_id):
    """
    make sure that cache with version of analyzers is not stale
    """
    if mock_config == 'rhel-9-beta-x86_64':
        # FIXME: hard-coded at two places for now
        mock_config = 'rhel-9-alpha-x86_64'
    if not AnalyzerVersion.objects.is_cache_uptodate(mock_config):
        session = ScanningSession.objects.get(id=scanning_session_id)
        analyzers = session.profile.analyzers
        csmock_args = session.profile.csmock_args
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
    if scan.can_have_base():
        task = Task.objects.get(id=task_id)
        scanning_session = ScanningSession.objects.get(id=task.args['scanning_session'])
        base_nvr = task.args['base_nvr']
        mock_config = scan.tag.mock.name
        if mock_config == 'rhel-9-beta-x86_64':
            # FIXME: hard-coded at two places for now
            mock_config = 'rhel-9-alpha-x86_64'
        logger.debug("Looking for base scan '%s', mock_config: %s", base_nvr, mock_config)
        try:
            base_scan = obtain_base(base_nvr, mock_config)
        except BaseNotValidException:
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
            base_task_args = prepare_base_scan(options, scanning_session)
            return base_task_args
        else:
            logger.info("Using cached base scan '%s'", base_scan)
            scan.set_base(base_scan)
    else:
        logger.info('Scan %s does not need base' % scan)


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
