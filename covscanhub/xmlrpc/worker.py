# -*- coding: utf-8 -*-


import logging

from kobo.hub.decorators import validate_worker
from kobo.hub.models import Task
from covscanhub.errata.scanner import prepare_base_scan, obtain_base2

from covscanhub.scan.service import extract_logs_from_tarball
from covscanhub.scan.models import ScanBinding
from covscanhub.service.processing import diff_results
from covscanhub.scan.notify import send_task_notification
from covscanhub.scan.xmlrpc_helper import finish_scan as h_finish_scan,\
    fail_scan as h_fail_scan, scan_notification_email
from covscanhub.scan.models import SCAN_STATES, Scan, TaskExtension, \
    SCAN_STATES_IN_PROGRESS, AppSettings

from django.core.exceptions import ObjectDoesNotExist


__all__ = (
    "email_task_notification",
    "email_scan_notification",
    "get_additional_arguments",
    "extract_tarball",
    "finish_scan",
    "fail_scan",
    "finish_task",
    "set_scan_to_scanning",
    "get_scanning_command",
    'create_sb',
)

logger = logging.getLogger(__name__)


@validate_worker
def extract_tarball(request, task_id, name):
    #name != None and len(name) > 0
    if name:
        extract_logs_from_tarball(task_id, name=name)
    else:
        extract_logs_from_tarball(task_id)


# REGULAR TASKS

@validate_worker
def email_task_notification(request, task_id):
    return send_task_notification(request, task_id)


@validate_worker
def finish_task(request, task_id):
    while True:
        # FIXME: implement this properly
        import time
        task = Task.objects.get(id=task_id)
        if task.is_finished():
            break
        time.sleep(10)
    if task.subtask_count == 1:
        base_task = task.subtasks()[0]
        task_dir = Task.get_task_dir(task.id)
        base_task_dir = Task.get_task_dir(base_task.id)
        return diff_results(task_dir, base_task_dir, task.label, base_task.label)
    elif task.subtask_count > 1:
        raise RuntimeError('Task %s contains too many subtasks' % task.id)


def get_additional_arguments(request, task_id):
    try:
        return TaskExtension.objects.get(task__id=task_id).secret_args
    except ObjectDoesNotExist:
        return None


# ET SCANS

@validate_worker
def email_scan_notification(request, scan_id):
    scan_notification_email(request, scan_id)


@validate_worker
def finish_scan(request, scan_id, task_id):
    h_finish_scan(request, scan_id, task_id)


@validate_worker
def set_scan_to_scanning(request, scan_id):
    scan = Scan.objects.get(id=scan_id)
    scan.set_state(SCAN_STATES['SCANNING'])
    if not scan.base:
        try:
            Scan.objects.get(
                state__in=SCAN_STATES_IN_PROGRESS,
                base=scan,
            ).set_state(SCAN_STATES['BASE_SCANNING'])
        except Exception, ex:
            logger.error("Can't find target for base %s: %s" % (scan, ex))


@validate_worker
def fail_scan(request, scan_id, reason=None):
    h_fail_scan(scan_id, reason)


@validate_worker
def get_scanning_command(request, scan_id):
    scan = Scan.objects.get(id=scan_id)
    if scan.is_errata_base_scan():
        rel_tag = scan.target.tag.release.tag
    else:
        rel_tag = scan.tag.release.tag
    return AppSettings.settings_scanning_command(rel_tag)


@validate_worker
def create_sb(request, task_id):
    task = Task.objects.get(id=task_id)
    scan = Scan.objects.get(id=task.args['scan_id'])
    ScanBinding.create_sb(task=task, scan=scan)


#@validate_worker
#def ensure_base_is_valid(request, scan, task):
#    """
#    Make sure that base is scanned properly, if not, do it (by spawning subtask)
#
#    we mean by valid that it has to be scanned by appropriate scanners
#    """
#    base_nvr = None
#    base = obtain_base2(base_nvr)
#    if not base:
#        options = {
#            'mock_config': task.args['mock_config'],
#            'target': task.args['base'],
#            'package_owner': scan.username.username,
#        }
#        spawn_subtask_args = prepare_base_scan(options)
#        return spawn
#        spawn_base
