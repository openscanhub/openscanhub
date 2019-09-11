#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
import os
import sys

PROJECT_DIR = '/var/'

if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

PROJECT_DIR2 = '/home/ttomecek/dev/covscan/'

if PROJECT_DIR2 not in sys.path:
    sys.path.append(PROJECT_DIR2)

KOBO_DIR = '/home/brq/ttomecek/dev/kobo'

if KOBO_DIR not in sys.path:
    sys.path.append(KOBO_DIR)

os.environ['DJANGO_SETTINGS_MODULE'] = 'covscanhub.settings'


from django.contrib.auth import get_user_model

from covscanhub.xmlrpc.worker import finish_scan, fail_scan, \
    email_scan_notification
from covscanhub.scan.models import Scan, ScanBinding, SCAN_TYPES, SCAN_STATES,\
    SCAN_TYPES_TARGET
from covscanhub.scan.service import extract_logs_from_tarball

from kobo.client.constants import TASK_STATES
from kobo.hub.models import Task

import shutil


from optparse import OptionParser


def set_options():
    parser = OptionParser()

    parser.add_option("-F", "--fail", help="fail scan",
                      action="store", type="int", dest="fail")

    parser.add_option("-f", "--finish", help="finish scan",
                      action="store", type="int", dest="finish")

    parser.add_option("-n", "--notify",
                      help="notify about scan being finished",
                      action="store", type="int", dest="notify")

    parser.add_option("-a", "--finish-all", help="finish all scans",
                      action="store_true", dest="finish_all")

    (options, args) = parser.parse_args()

    return parser, options, args


class FakeRequest(object):
    def __init__(self):
        self.user = get_user_model().objects.get(
            username='worker/covscan-stage.lab.eng.brq2.redhat.com')
        self.worker = 'asd'
        self.META = {}
        self.META['REMOTE_ADDR'] = 'covscan-stage.lab.eng.brq2.redhat.com'


def m_finish_scan(scan_id):
    sb = ScanBinding.objects.get(scan=Scan.objects.get(id=scan_id),
                                 task__state=TASK_STATES['FREE'])
    task_dir = Task.get_task_dir(sb.task.id)

    source_path = '/tmp/covscanhub'
    dir_list = os.listdir(source_path)

    final_dir = ''
    for d in dir_list:
        if sb.scan.nvr in d and '.tar.' in d:
            final_dir = d
            break
    if not final_dir:
        raise RuntimeError('Cannot find tarball with results for %s.' %
                           sb.scan.nvr)

    shutil.copy(os.path.join(source_path, final_dir), task_dir)

    extract_logs_from_tarball(sb.task.id)

    print('Finishing scan %s' % sb.scan.nvr)
    finish_scan(FakeRequest(), scan_id, sb.task.id)

    Task.objects.filter(id=sb.task.id).update(state=TASK_STATES['CLOSED'])


def m_fail_scan(scan_id):
    fail_scan(FakeRequest(), scan_id, "Scan set to failed from CLI")


def m_email_scan_notification(scan_id):
    email_scan_notification(FakeRequest(), scan_id)


def m_finish_all_scans():
    base_scans = Scan.objects.filter(scan_type=SCAN_TYPES['ERRATA_BASE'],
                                     state=SCAN_STATES['QUEUED'])
    for base in base_scans:
        m_finish_scan(base.id)
    target_scans = Scan.objects.filter(scan_type__in=SCAN_TYPES_TARGET,
                                       state=SCAN_STATES['QUEUED'])
    for target in target_scans:
        m_finish_scan(target.id)


if __name__ == '__main__':
    parser, options, args = set_options()

    if options.finish:
        m_finish_scan(options.finish)
    elif options.finish_all:
        m_finish_all_scans()
    elif options.fail:
        m_fail_scan(options.fail)
    elif options.notify:
        m_email_scan_notification(options.notify)
    else:
        parser.error('You haven\'t specified any option.')
