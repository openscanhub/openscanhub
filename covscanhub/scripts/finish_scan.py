#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

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


from django.contrib.auth.models import User

from covscanhub.xmlrpc.worker import finish_scan
from covscanhub.scan.models import Scan, ScanBinding
from covscanhub.scan.service import extract_logs_from_tarball

from kobo.client.constants import TASK_STATES
from kobo.hub.models import Task

import shutil


class FakeRequest(object):
    def __init__(self):
        self.user = User.objects.get(
            username='worker/uqtm.lab.eng.brq.redhat.com')
        self.worker = 'asd'
        self.META = {}
        self.META['REMOTE_ADDR'] = 'uqtm.lab.eng.brq.redhat.com'


def main():
    try:
        scan_id = int(sys.argv[1])
    except ValueError:
        print 'Invalid ID.'
        sys.exit(1)
    except IndexError:
        print "You haven't provided ID of scan."
        sys.exit(2)
    
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
    
    shutil.copy(os.path.join(source_path, final_dir), task_dir)    
    
    extract_logs_from_tarball(sb.task.id)
    
    print 'Finishing scan %s' % sb.scan.nvr
    finish_scan(FakeRequest(), scan_id, sb.task.id)

    Task.objects.filter(id=sb.task.id).update(state=TASK_STATES['CLOSED'])

if __name__ == '__main__':
    main()
