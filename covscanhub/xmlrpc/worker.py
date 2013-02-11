# -*- coding: utf-8 -*-


from kobo.hub.decorators import validate_worker
from kobo.hub.models import Task

from covscanhub.scan.service import extract_logs_from_tarball, \
    update_scans_state, prepare_and_execute_diff
from covscanhub.scan.notify import send_task_notification, \
    send_scan_notification
from covscanhub.scan.models import SCAN_STATES, SCAN_TYPES, Scan
from covscanhub.scan.xmlrpc_helper import finish_scan as h_finish_scan,\
    fail_scan as h_fail_scan


__all__ = (
    "email_task_notification",
    "email_scan_notification",
    "extract_tarball",
    "finish_scan",
    "fail_scan",
    "finish_task",
    "set_scan_to_scanning",
)


@validate_worker
def email_task_notification(request, task_id):
    return send_task_notification(request, task_id)


@validate_worker
def email_scan_notification(request, scan_id):
    scan = Scan.objects.get(id=scan_id)
    if scan.scan_type == SCAN_TYPES['ERRATA']:
        if scan.state != SCAN_STATES['FAILED'] and scan.state != SCAN_STATES['CANCELED']:
            return send_scan_notification(request, scan_id)


@validate_worker
def extract_tarball(request, task_id, name):
    #name != None and len(name) > 0
    if name:
        extract_logs_from_tarball(task_id, name=name)
    else:
        extract_logs_from_tarball(task_id)


@validate_worker
def finish_scan(request, scan_id, task_id):
    h_finish_scan(scan_id, task_id)


@validate_worker
def finish_task(request, task_id):
    task = Task.objects.get(id=task_id)
    if task.subtask_count == 1:
        child_task = task.subtasks()[0]
        prepare_and_execute_diff(task, child_task, task.label,
                                 child_task.label)
    elif task.subtask_count > 1:
        raise RuntimeError('Task %s contains too much subtasks' % task.id)


@validate_worker
def set_scan_to_scanning(request, scan_id):
    update_scans_state(scan_id, SCAN_STATES['SCANNING'])
    scan = Scan.objects.get(id=scan_id)
    if scan.parent:
        Scan.objects.filter(id=scan.parent.id)\
            .update(state=SCAN_STATES['BASE_SCANNING'])


@validate_worker
def fail_scan(request, scan_id, reason=None):
    h_fail_scan(scan_id, reason)
