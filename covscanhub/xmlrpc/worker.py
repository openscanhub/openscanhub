# -*- coding: utf-8 -*-


import kobo.hub.xmlrpc.client

from kobo.client.constants import TASK_STATES
from kobo.hub.decorators import validate_worker
from kobo.hub.models import Task
from covscanhub.scan.service import extract_logs_from_tarball, \
    update_scans_state
from covscanhub.errata.service import finish_scanning
from covscanhub.scan.models import SCAN_STATES

__all__ = (
    "email_task_notification",
    "extract_tarball",
    "set_scan_to_scanning",
    "finish_scan",
)


@validate_worker
def email_task_notification(request, task_id):
    import socket
    from django.core.mail import get_connection, EmailMessage
    connection = get_connection(fail_silently=False)

    task = Task.objects.get(id=task_id)
    recipient = task.owner.username
    if "@" not in recipient:
        if recipient == "admin":
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
    if name is not None and name:
        extract_logs_from_tarball(task_id, name=name)
    else:
        extract_logs_from_tarball(task_id)


@validate_worker
def finish_scan(request, scan_id):
    finish_scanning(scan_id)


@validate_worker
def set_scan_to_scanning(request, scan_id):
    update_scans_state(scan_id, SCAN_STATES['SCANNING'])


#@validate_worker
#def set_scan_to_finished(request, scan_id):
#    update_scans_state(scan_id, SCAN_STATES['WAIVED'])
#
#
#@validate_worker
#def set_scan_to_needs_insp(request, scan_id):
#    update_scans_state(scan_id, SCAN_STATES['NEEDS_INSPECTION'])
#
#
#@validate_worker
#def run_diff_on_scans(request, scan_id):
#    """
#        XML-RPC
#    """
#    run_diff(scan_id)