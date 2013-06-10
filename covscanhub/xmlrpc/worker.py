# -*- coding: utf-8 -*-


import logging

from kobo.hub.decorators import validate_worker
from kobo.hub.models import Task

from covscanhub.scan.service import extract_logs_from_tarball, \
    prepare_and_execute_diff
from covscanhub.scan.notify import send_task_notification
from covscanhub.scan.xmlrpc_helper import finish_scan as h_finish_scan,\
    fail_scan as h_fail_scan, scan_notification_email
from covscanhub.scan.models import SCAN_STATES, Scan, TaskExtension

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
    task = Task.objects.get(id=task_id)
    if task.subtask_count == 1:
        child_task = task.subtasks()[0]
        prepare_and_execute_diff(task, child_task, task.label,
                                 child_task.label)
    elif task.subtask_count > 1:
        raise RuntimeError('Task %s contains too much subtasks' % task.id)


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
                state=SCAN_STATES['QUEUED'],
                base=scan,
            ).set_state(SCAN_STATES['BASE_SCANNING'])
        except Exception, ex:
            logger.error("Can't find target for base %s: %s" % (scan, ex))


@validate_worker
def fail_scan(request, scan_id, reason=None):
    h_fail_scan(scan_id, reason)
