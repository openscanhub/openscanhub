# -*- coding: utf-8 -*-


import os
import logging

from kobo.hub.decorators import validate_worker
from kobo.hub.models import Task
from covscand.tasks.common import construct_cim_string
from covscanhub.errata.models import ScanningSession
from covscanhub.errata.scanner import prepare_base_scan, obtain_base2, BaseNotValidException
from covscanhub.other.decorators import public

from covscanhub.scan.models import ScanBinding, AnalyzerVersion
from covscanhub.service.csmock_parser import CsmockAPI, unpack_and_return_api
from covscanhub.scan.notify import send_task_notification
from covscanhub.scan.xmlrpc_helper import finish_scan as h_finish_scan,\
    fail_scan as h_fail_scan, scan_notification_email, prepare_version_retriever
from covscanhub.scan.models import SCAN_STATES, Scan, TaskExtension, \
    SCAN_STATES_IN_PROGRESS, AppSettings

from django.core.exceptions import ObjectDoesNotExist
from covscanhub.waiving.results_loader import TaskResultsProcessor


logger = logging.getLogger(__name__)


# REGULAR TASKS

@validate_worker
@public
def email_task_notification(request, task_id):
    return send_task_notification(request, task_id)


@validate_worker
@public
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
        return td.generate_diffs()


@validate_worker
@public
def get_cim_arg(request, task_id):
    try:
        cim_dict = TaskExtension.objects.get(task__id=task_id).secret_args
    except ObjectDoesNotExist:
        return None
    else:
        cim_str = construct_cim_string(cim_dict)
        return "--cov-commit-to '%s'" % cim_str

# ET SCANS

@validate_worker
@public
def email_scan_notification(request, scan_id):
    scan_notification_email(request, scan_id)


@validate_worker
@public
def finish_scan(request, scan_id, filename):
    h_finish_scan(request, scan_id, filename)


@validate_worker
@public
def finish_analyzers_version_retrieval(request, task_id, filename):
    task = Task.objects.get(id=task_id)
    task_dir = Task.get_task_dir(task_id)
    tb_path = os.path.join(task_dir, filename)
    csmock = unpack_and_return_api(tb_path, task_dir)
    analyzers = csmock.get_analyzers()
    mock_config = task.args['mock_config']
    AnalyzerVersion.objects.update_analyzers_versions(analyzers, mock_config)


@validate_worker
@public
def get_su_user(request):
    return None


@validate_worker
@public
def set_scan_to_basescanning(request, scan_id):
    scan = Scan.objects.get(id=scan_id)
    scan.set_state_basescanning()


@validate_worker
@public
def set_scan_to_scanning(request, scan_id):
    scan = Scan.objects.get(id=scan_id)
    scan.set_state_scanning()


@validate_worker
@public
def fail_scan(request, scan_id, reason=None):
    h_fail_scan(scan_id, reason)


@validate_worker
@public
def get_scanning_args(request, scanning_session_id):
    scanning_session = ScanningSession.objects.get(id=scanning_session_id)
    return scanning_session.profile.command_arguments


@validate_worker
@public
def create_sb(request, task_id):
    task = Task.objects.get(id=task_id)
    scan = Scan.objects.get(id=task.args['scan_id'])
    ScanBinding.create_sb(task=task, scan=scan)


@validate_worker
@public
def ensure_cache(request, mock_config, scanning_session_id):
    """
    make sure that cache with version of analyzers is not stale
    """
    if not AnalyzerVersion.objects.is_cache_uptodate(mock_config):
        analyzers = ScanningSession.objects.get_analyzers(scanning_session_id)
        su_user = AppSettings.setting_get_su_user()
        return prepare_version_retriever(mock_config, analyzers, su_user)


@validate_worker
@public
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
        logger.debug("Looking for base scan '%s'.", base_nvr)
        try:
            base_scan = obtain_base2(base_nvr)
        except BaseNotValidException:
            logger.info("Preparing base scan")
            options = {
                'mock_config': scan.tag.mock.name,
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

