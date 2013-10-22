# -*- coding: utf-8 -*-
"""functions related to sending e-mail notifications"""

import socket
import logging

from django.core.mail import get_connection, EmailMessage
from django.core.urlresolvers import reverse

import kobo.hub.xmlrpc.client
from kobo.hub.models import Task
from kobo.client.constants import TASK_STATES

from covscanhub.scan.models import Scan, SCAN_STATES
from covscanhub.scan.models import AppSettings
from covscanhub.service.loading import load_defects, get_defect_stats
from covscanhub.waiving.service import get_scans_new_defects_count

__all__ = (
    "send_task_notification",
    "send_scan_notification",
)


logger = logging.getLogger(__name__)


def send_mail(message, recipient, subject, recipients, headers, bcc=None):
    connection = get_connection(fail_silently=False)

    from_addr = "<covscan-auto@redhat.com>"

    headers["X-Application-ID"] = "covscan"
    headers["X-Hostname"] = socket.gethostname()

    return EmailMessage(subject, message, from_addr, recipients, bcc=bcc,
                        headers=headers, connection=connection).send()


def get_recipient(user):
    """
    parameter: django's User model,
    return e-mail address to send e-mail to
    """
    if "@" not in user.username:
        if user.username == "admin" or user.username == "test":
            recipient = None
        else:
            if user.email:
                recipient = user.email
            else:
                # XXX: hardcoded
                recipient = user.username + "@redhat.com"
    else:
        recipient = user.username
    return recipient


def generate_stats(task, diff_task):
    def display_defects(result_list, label_name, defects_dict, diff_sign=''):
        if defects_dict:
            result_list.append(label_name)
            result_list += ["%s: %s%d" % (checker, diff_sign, count) for checker, count in defects_dict.items()]
        return result_list
    defects_json = load_defects(task.id)
    stats = get_defect_stats(defects_json)
    result = []
    if diff_task:
        added = stats['added']
        fixed = stats['fixed']
        display_defects(result, "Added:", added, '+')
        display_defects(result, "Fixed:", fixed, '-')
    else:
        defects = stats['defects']
        display_defects(result, 'All defects:', defects)
    return '\n'.join(result)


def send_task_notification(request, task_id):
    task = Task.objects.get(id=task_id)

    # return if task has some parent and send e-mail only from parent task
    if task.parent:
        return
    state = TASK_STATES.get_value(task.state)
    recipient = get_recipient(task.owner)
    hostname = socket.gethostname()
    task_url = kobo.hub.xmlrpc.client.task_url(request, task_id)

    try:
        nvr = task.args['brew_build']
        source = "Brew Build"
        package = task.args['brew_build']
    except KeyError:
        nvr = task.args['srpm_name'][:-8]
        source = "SRPM"
        package = task.args['srpm_name']

    message = [
        "Hostname: %s" % hostname,
        "Task ID: %s" % task_id,
        "%s: %s" % (source, package),
        "Task state: %s" % state,
        "Task owner: %s" % task.owner.username,
        "Task method: %s" % task.method,
        "",
        "Task URL: %s" % task_url,
        "Comment: %s" % task.comment or "",
        "",
        "%s" % generate_stats(task.id, task.method not in ['MockBuild', 'DiffBuild']),
    ]
    message = "\n".join(message)

    subject = "Task [#%s] %s finished, state: %s" % (task_id, nvr, state)

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
        "X-Scan-Build": nvr,
    }

    return send_mail(message, recipient, subject, recipients, headers, bcc)


class MailGenerator(object):
    def __init__(self, request, scan):
        self.request = request
        self.scan = scan
        self.scan_state = SCAN_STATES.get_value(scan.state)

    def get_scans_url(self):
        """Return complete URL to waiver of provided scan"""
        return self.request.build_absolute_uri(
            reverse('waiving/result', args=(self.scan.scanbinding.id, )))

    def generate_failed_scan_text(self):
        """return e-mail's message for failed scans"""
        return """Scan of %(nvr)s failed.

URL: %(url)s""" % {'url': self.get_scans_url(), 'nvr': self.scan.nvr}

    def generate_general_text(self, display_states=True):
        message = [
            "%(firstline)s",
            "",
            "Scan state: %s" % self.scan_state,
            "Waiver URL: %s" % self.get_scans_url(),
            "New defects count: %d" % get_scans_new_defects_count(self.scan.id),
            "%s" % generate_stats(self.scan.scanbinding.task, True),
            "",
            "%(guide_message)s",
        ]
        message = "\n".join(message)
        if display_states:
            message += """
    Is a bug -- defect is true positive and you are going to fix it (with \
next build)
    Fix later -- defect is true positive, but fix is postponed to next release
    Not a bug -- issue is false positive, so you are waiving it
            """
        message += """
You can find documentation of covscan's workflow at \
http://cov01.lab.eng.brq.redhat.com/covscan_documentation.html .

If you have any questions, feel free to ask at Red Hat IRC channel #coverity \
or coverity-users@redhat.com .
"""
        return message

    def generate_rebase_scan_text(self):
        return self.generate_general_text() % {
            'firstline': "Automatic static analysis scan of build %s \
submitted from Errata Tool has finished." % (self.scan.nvr),
            'guide_message': "You've been doing rebase, this means that \
number of newly added defects might be high and it would take too long to \
check (and fix) them all. Please fix most serious ones and/or discuss the \
results with upstream. Here is a description of states:"
        }

    def generate_regular_scan_text(self):
        return self.generate_general_text() % {
            'firstline': "Automatic static analysis scan of build %s \
submitted from Errata Tool has finished." % (self.scan.nvr),
            'guide_message': "There were found some issues by differential \
scan. These were probably introduced by some patch and should be fixed right \
away. There is a possibility that some of the issues might be false \
positives, so please mark or waive the defect groups. Here is a description \
of states:"
        }

    def generate_disputed_scan_text(self):
        return self.generate_general_text() % {
            'firstline': "Someone has disputed a scan of %s, which you \
own. It means that one of the waivers was invalidated. If you have done \
it, consider this e-mail as informational. If this was done by someone else, \
please check the run." % (self.scan.nvr),
            'guide_message': "Please, check the invalidated group of defects \
and waive it. Here is a description of states:"
        }

    def generate_newpkg_scan_text(self):
        return self.generate_general_text() % {
            'firstline': "Automatic static analysis scan of build %s \
submitted from Errata Tool has finished." % (self.scan.nvr),
            'guide_message': "This is a scan of newly added package. covscan \
therefore has no base to diff against. This means that final report is a list \
of all defects found by covscan. The list may be really big. Please fix most \
serious ones and/or discuss the results with upstream. Here is a description \
of states:"
        }

    def generate_new_comment_text(self, commenter, date, message):
        return self.generate_general_text(display_states=False) % {
            'firstline': "New comment has been added to scan of package %s." %
            (self.scan.nvr),
            'guide_message': "Comment from %s posted on %s:\n\n%s\n" % (
                commenter,
                date.strftime('%Y-%m-%d %H:%M:%S'), # TODO: add %Z - TZ
                message
            )
        }


def send_scan_notification(request, scan_id):
    scan = Scan.objects.get(id=scan_id)
    mg = MailGenerator(request, scan)

    # recipient setting
    recipient = "covscan-auto@redhat.com"
    if AppSettings.setting_send_mail():
        recipient = get_recipient(scan.username)

    # message setting
    if scan.is_failed() or scan.is_canceled():
        message = mg.generate_failed_scan_text()
    elif scan.is_disputed():
        message = mg.generate_disputed_scan_text()
    elif scan.is_newpkg_scan():
        message = mg.generate_newpkg_scan_text()
    elif scan.is_rebase_scan():
        # rebase should be after disputed, so 'disputing' e-mails are being
        # sent for rebases
        message = mg.generate_rebase_scan_text()
    else:
        message = mg.generate_regular_scan_text()

    # subject setting
    if scan.is_disputed():
        subject = "[covscan] Scan of %s has been disputed" % (scan.nvr)
    else:
        subject = "[covscan] Scan of %s finished, state: %s" % (scan.nvr,
                                                                mg.scan_state)

    headers = {
        "X-Scan-ID": scan.scanbinding.id,
        "X-Scan-State": mg.scan_state,
        "X-Scan-Package": scan.package.name,
        "X-Scan-Build": scan.nvr,
    }
    return send_mail(message, recipient, subject, [recipient], headers=headers)


def send_notif_new_comment(request, scan, wl):
    mg = MailGenerator(request, scan)

    if AppSettings.setting_send_mail():
        recipient = get_recipient(scan.username)
    else:
        recipient = "ttomecek@redhat.com"

    logger.info('Notifying %s about new comment in %s', recipient, scan.nvr)

    message = mg.generate_new_comment_text(wl.user, wl.date, wl.waiver.message)

    subject = "[covscan] New comment has been added to scan of %s" % (scan.nvr)

    headers = {
        "X-Scan-ID": scan.scanbinding.id,
        "X-Scan-State": mg.scan_state,
        "X-Scan-Package": scan.package.name,
        "X-Scan-Build": scan.nvr,
    }
    return send_mail(message, recipient, subject, [recipient], headers=headers)
