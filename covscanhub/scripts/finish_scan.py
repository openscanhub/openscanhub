# -*- coding: utf-8 -*-

import os
import sys

PROJECT_DIR = '/var/'

if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

KOBO_DIR = '/home/brq/ttomecek/dev/kobo'

if KOBO_DIR not in sys.path:
    sys.path.append(KOBO_DIR)

os.environ['DJANGO_SETTINGS_MODULE'] = 'covscanhub.settings'


from covscanhub.xmlrpc.worker import finish_scan
from django.contrib.auth.models import User


class FakeRequest(object):
    def __init__(self):
        self.user = User.objects.get(
            username='worker/uqtm.lab.eng.brq.redhat.com')
        self.worker = 'asd'
        self.META = {}
        self.META['REMOTE_ADDR'] = 'uqtm.lab.eng.brq.redhat.com'

print finish_scan(FakeRequest(), 2)
