# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

"""functions related to sending e-mail notifications"""

import logging
import socket

import kobo.hub.xmlrpc.client
from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.urls import reverse
from kobo.client.constants import TASK_STATES
from kobo.hub.models import Task

from osh.hub.scan.models import SCAN_STATES, AppSettings, Scan
from osh.hub.service.loading import get_defect_stats, load_defects
from osh.hub.waiving.service import get_scans_new_defects_count

__all__ = (
    "send_task_notification",
    "send_scan_notification",
)


logger = logging.getLogger(__name__)


def send_mail(message, subject, recipients, headers, bcc=None):
    connection = get_connection(fail_silently=False)

    if not AppSettings.setting_send_mail():
        # mail just admins if AppSettings/SEND_MAIL is disabled
        recipients = [a[1] for a in settings.ADMINS]

    from_addr = settings.NOTIFICATION_EMAIL_ADDRESS

    headers["X-Application-ID"] = "OpenScanHub"
    headers["X-Hostname"] = socket.gethostname()

    return EmailMessage(subject, message, from_addr, recipients, bcc=bcc,
                        headers=headers, connection=connection).send()


def get_recipient(user):
    """
    parameter: django's User model,
    return e-mail address to send e-mail to
    """
    if "@" in user.username:
        return user.username

    if user.username in ("admin", "test"):
        return None

    if user.email:
        return user.email

    # XXX: hardcoded
    return user.username + "@redhat.com"


def generate_stats(task, diff_task=False, with_defects_in_patches=False):
    def display_defects(result_list, label_name, defects_dict, diff_sign=''):
        if defects_dict:
            result_list.append('')
            if label_name:
                result_list.append(label_name)
                result_list.append('')
            sorted_list = sorted(list(defects_dict.items()), key=lambda x: x[0])
            result_list += ["%-25s %s%d" % (checker, diff_sign, count) for checker, count in sorted_list]
            result_list.append('')
        return result_list
    try:
        defects_json = load_defects(task.id, diff_task)
    except RuntimeError:
        return ''
    result = []
    if diff_task:
        added = get_defect_stats(defects_json['added'])
        fixed = get_defect_stats(defects_json['fixed'])
        display_defects(result, "Added (+), Fixed (-)", added, '+')
        display_defects(result, "", fixed, '-')
    elif with_defects_in_patches:
        defects = get_defect_stats(defects_json['defects'])
        display_defects(result, 'Defects in patches', defects)
    else:
        defects = get_defect_stats(defects_json['defects'])
        display_defects(result, 'All defects', defects)
    return '\n'.join(result)


def send_task_notification(request, task_id):
    task = Task.objects.get(id=task_id)

    # return if task has some parent and send e-mail only from parent task
    if task.parent:
        return
    state = TASK_STATES.get_value(task.state)
    if not task.is_finished():
        logger.warning("Not sending e-mail for task %d with state '%s'", task_id, state)
        return
    recipient = get_recipient(task.owner)
    hostname = socket.gethostname()
    task_url = kobo.hub.xmlrpc.client.task_url(request, task_id)

    try:
        build = task.args['build']
        source = "Build"
        package = build.get("nvr", None)
    except KeyError:
        source = "SRPM"
        package = task.args['srpm_name']

    if task.method == 'MockBuild':
        stats = generate_stats(task, diff_task=False, with_defects_in_patches=False)
    elif task.method == 'DiffBuild':
        stats = generate_stats(task, diff_task=False, with_defects_in_patches=True)
    elif task.method == 'VersionDiffBuild':
        stats = generate_stats(task, diff_task=True, with_defects_in_patches=False)
    else:
        return

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
        "%s" % stats,
    ]
    message = "\n".join(message)

    subject = "Task [#%s] %s finished, state: %s" % (task_id, package, state)

    to = task.args.get("email_to", []) or []
    recipients = set()
    if recipient:
        recipients.add(recipient)
    if to:
        recipients.update(to)

    if task.is_failed():
        recipients.add(settings.DEVEL_EMAIL_ADDRESS)

    if not recipients:
        return

    headers = {
        "X-Task-ID": task_id,
        "X-Task-State": state,
        "X-Task-Owner": task.owner.username,
        "X-Scan-Build": package,
    }

    return send_mail(message, subject, recipients, headers)


class MailGenerator:
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
            "%s" % generate_stats(self.scan.scanbinding.task, not self.scan.is_newpkg_scan()),
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
You can find documentation of OpenScanHub's workflow at \
https://cov01.lab.eng.brq2.redhat.com/covscan_documentation.html .
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
            'guide_message': "This is a scan of newly added package. OpenScanHub \
therefore has no base to diff against. This means that final report is a list \
of all defects found by OpenScanHub. The list may be really big. Please fix most \
serious ones and/or discuss the results with upstream. Here is a description \
of states:"
        }

    def generate_new_comment_text(self, commenter, date, message):
        return self.generate_general_text(display_states=False) % {
            'firstline': "New comment has been added to scan of package %s." %
            (self.scan.nvr),
            'guide_message': "Comment from %s posted on %s:\n\n%s\n" % (
                commenter,
                date.strftime('%Y-%m-%d %H:%M:%S'),  # TODO: add %Z - TZ
                message
            )
        }


def send_scan_notification(request, scan_id):
    scan = Scan.objects.get(id=scan_id)
    mg = MailGenerator(request, scan)

    # recipient setting
    recipient = get_recipient(scan.username)

    # message setting
    if scan.is_failed() or scan.is_canceled():
        recipient = settings.DEVEL_EMAIL_ADDRESS
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
        subject = "[OpenScanHub] Scan of %s has been disputed" % (scan.nvr)
    else:
        subject = "[OpenScanHub] Scan of %s finished, state: %s" % (scan.nvr, mg.scan_state)

    headers = {
        "X-Scan-ID": scan.scanbinding.id,
        "X-Scan-State": mg.scan_state,
        "X-Scan-Package": scan.package.name,
        "X-Scan-Build": scan.nvr,
    }
    return send_mail(message, subject, [recipient], headers)


def send_notif_new_comment(request, scan, wl):
    mg = MailGenerator(request, scan)

    recipient = get_recipient(scan.username)

    logger.info('Notifying %s about new comment in %s', recipient, scan.nvr)

    message = mg.generate_new_comment_text(wl.user, wl.date, wl.waiver.message)

    subject = "[OpenScanHub] New comment has been added to scan of %s" % (scan.nvr)

    headers = {
        "X-Scan-ID": scan.scanbinding.id,
        "X-Scan-State": mg.scan_state,
        "X-Scan-Package": scan.package.name,
        "X-Scan-Build": scan.nvr,
    }
    return send_mail(message, subject, [recipient], headers)
