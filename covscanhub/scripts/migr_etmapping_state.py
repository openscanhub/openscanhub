# -*- coding: utf-8 -*-

import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

os.environ['DJANGO_SETTINGS_MODULE'] = 'covscanhub.settings'

from covscanhub.waiving.models import ETMapping, REQUEST_STATES

for etm in ETMapping.objects.all():
    if etm.latest_run:
        etm.state = REQUEST_STATES.get_value("OK")
        etm.save()
    else:
        etm.state = REQUEST_STATES.get_value("INELIGIBLE")
        etm.save()
