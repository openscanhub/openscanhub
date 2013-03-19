# -*- coding: utf-8 -*-
"""functions related to sending notifications"""

import socket

from django.core.mail import get_connection, EmailMessage
from django.core.urlresolvers import reverse

import kobo.hub.xmlrpc.client
from kobo.hub.models import Task
from kobo.client.constants import TASK_STATES

from covscanhub.scan.models import Scan, SCAN_STATES
from covscanhub.scan.models import AppSettings


__all__ = (
    "send_task_notification",
    "send_scan_notification",
)


def send_mail(message, recipient, subject, recipients, headers, bcc=None):
    connection = get_connection(fail_silently=False)

    # XXX: hardcoded
    from_addr = "Coverity Results mailing list <coverity-results@redhat.com>"

    headers["X-Application-ID"] = "covscan"
    headers["X-Hostname"] = socket.gethostname()

    return EmailMessage(subject, message, from_addr, recipients, bcc=bcc,
                        headers=headers, connection=connection).send()


def get_recipient(recipient):
    if "@" not in recipient:
        if recipient == "admin" or recipient == "test":
            recipient = None
        else:
            # XXX: hardcoded
            recipient += "@redhat.com"
    return recipient


def send_task_notification(request, task_id):
    task = Task.objects.get(id=task_id)
    state = TASK_STATES.get_value(task.state)
    recipient = get_recipient(task.owner.username)
    hostname = socket.gethostname()
    task_url = kobo.hub.xmlrpc.client.task_url(request, task_id)
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
    subject = "Task [#%s] finished, state: %s" % (task_id, state)

    to = task.args.get("email_to", []) or []
    bcc = task.args.get("email_bcc", []) or []
    recipients = []
    if recipient:
        recipients.append(recipient)
    if to:
        recipients.extend(to)
    if not recipients and not bcc:
        return

    headers = {
        "X-Task-ID": task_id,
        "X-Task-State": state,
        "X-Task-Owner": task.owner.username,
    }

    return send_mail(message, recipient, subject, recipients, headers, bcc)


def send_scan_notification(request, scan_id):
    scan = Scan.objects.get(id=scan_id)
    state = SCAN_STATES.get_value(scan.state)
    if AppSettings.setting_send_mail():
        recipient = get_recipient(scan.username.username)
    else:
        recipient = "ttomecek@redhat.com"

    message = [
        "Scan of a package %s have finished:" % scan.package.name,
        # "Waiver ID: %s" % scan.scanbinding.id,
        "Scan state: %s" % state,
        "",
        "Waiver URL: %s" % request.build_absolute_uri(
            reverse('waiving/result', args=(scan.scanbinding.id, ))
        ),
    ]
    message = "\n".join(message)
    message += """
There is possibility that some of the issues might be false positives. So \
please mark them accordingly:
    Is a bug -- defect is true positive and you are going to fix it (with \
next build)
    Fix later -- defect is true positive, but fix is postponed to next release
    Not a bug -- issue is false positive, so you are waiving it

You can find documentation of covscan's workflow at \
http://cov01.lab.eng.brq.redhat.com/covscan_documentation.html

If you have any questions, feel free to ask at #coverity or \
coverity-users@redhat.com
"""
    subject = "Scan of %s finished, state: %s" % (scan.nvr, state)

    headers = {
        "X-Scan-ID": scan.scanbinding.id,
        "X-Scan-State": state,
    }

    return send_mail(message, recipient, subject, [recipient], headers=headers)
