# -*- coding: utf-8 -*-


import kobo.hub.xmlrpc.client

from kobo.client.constants import TASK_STATES
from kobo.hub.decorators import validate_worker
from kobo.hub.models import Task


__all__ = (
    "email_task_notification",
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
