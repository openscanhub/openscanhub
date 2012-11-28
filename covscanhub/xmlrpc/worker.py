# -*- coding: utf-8 -*-


import kobo.hub.xmlrpc.client

from kobo.client.constants import TASK_STATES
from kobo.hub.decorators import validate_worker
from kobo.hub.models import Task

from covscanhub.other.exceptions import ScanException
from covscanhub.scan.service import extract_logs_from_tarball, \
    update_scans_state, prepare_and_execute_diff, post_qpid_message, \
    get_latest_binding
from covscanhub.waiving.service import create_results, get_unwaived_rgs
from covscanhub.scan.models import SCAN_STATES, Scan, ScanBinding

__all__ = (
    "email_task_notification",
    "extract_tarball",
    "finish_scan",
    "finish_task",
    "set_scan_to_scanning",
)


@validate_worker
def email_task_notification(request, task_id):
    import socket
    from django.core.mail import get_connection, EmailMessage
    connection = get_connection(fail_silently=False)

    task = Task.objects.get(id=task_id)
    recipient = task.owner.username
    if "@" not in recipient:
        if recipient == "admin" or recipient == "test":
            recipient = None
        else:
            # XXX: hardcoded
            recipient += "@redhat.com"

    state = TASK_STATES.get_value(task.state)
    to = task.args.get("email_to", []) or []
    bcc = task.args.get("email_bcc", []) or []

    task_url = kobo.hub.xmlrpc.client.task_url(request, task_id)

    # XXX: hardcoded
    from_addr = "Coverity Results mailing list <coverity-results@redhat.com>"
    recipients = []
    if recipient:
        recipients.append(recipient)
    if to:
        recipients.extend(to)
    if not recipients and not bcc:
        return
    subject = "Task [#%s] finished, state: %s" % (task_id, state)
    hostname = socket.gethostname()
    message = [
        "Hostname: %s" % hostname,
        "Task ID: %s" % task_id,
        "Task state: %s" % state,
        "Task owner: %s" % task.owner.username,
        "Task method: %s" % task.method,
        "",
        "Task URL: %s" % task_url,
        "Comment: %s" % task.comment or "",
    ]
    message = "\n".join(message)

    headers = {
        "X-Application-ID": "covscan",
        "X-Hostname": hostname,
        "X-Task-ID": task_id,
        "X-Task-State": state,
        "X-Task-Owner": task.owner.username,
    }

    return EmailMessage(subject, message, from_addr, recipients, bcc=bcc, headers=headers, connection=connection).send()


@validate_worker
def extract_tarball(request, task_id, name):
    #name != None and len(name) > 0
    if name:
        extract_logs_from_tarball(task_id, name=name)
    else:
        extract_logs_from_tarball(task_id)


@validate_worker
def finish_scan(request, scan_id, task_id):
    sb = ScanBinding.objects.get(scan=scan_id, task=task_id)
    scan = Scan.objects.get(id=sb.scan.id)
    
    if sb.task.state == TASK_STATES['FAILED'] or \
            sb.task.state == TASK_STATES['CANCELED']:
        scan.state = SCAN_STATES['FAILED']
        scan.enabled = False
    else:
        if scan.is_errata_scan() and scan.base:
            try:
                prepare_and_execute_diff(sb.task,
                                     get_latest_binding(scan.base).task,
                                     scan.nvr, scan.base.nvr)
            except ScanException:
                scan.state = SCAN_STATES['FAILED']
                scan.save()
                return

        result = create_results(scan, sb)
    
        if scan.is_errata_scan():
            # if there are no missing waivers = there some newly added unwaived
            # defects
            if not get_unwaived_rgs(result):
                scan.state = SCAN_STATES['PASSED']
            else:
                scan.state = SCAN_STATES['NEEDS_INSPECTION']
    
            post_qpid_message(sb.id, SCAN_STATES.get_value(scan.state))
        elif scan.is_errata_base_scan():
            scan.state = SCAN_STATES['FINISHED']
    scan.save()


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
def fail_scan(request, scan_id, reason):
    update_scans_state(scan_id, SCAN_STATES['FAILED'])
    if reason:
        scan = Scan.objects.get(id=scan_id)
        Task.objects.filter(id=scan.task.id).update(
            result="Scan failed due to: %s" % reason)