# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

os.environ['DJANGO_SETTINGS_MODULE'] = 'covscanhub.settings'

from covscanhub.scan.models import ETMapping, REQUEST_STATES

for etm in ETMapping.objects.all():
    if etm.latest_run:
        etm.state = REQUEST_STATES["OK"]
        etm.save()
    else:
        etm.state = REQUEST_STATES["INELIGIBLE"]
        etm.save()
