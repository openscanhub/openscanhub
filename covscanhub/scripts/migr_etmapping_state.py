# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

from covscanhub.scan.models import REQUEST_STATES, ETMapping

PROJECT_DIR = Path(__file__).parents[2]

if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

os.environ['DJANGO_SETTINGS_MODULE'] = 'covscanhub.settings'

for etm in ETMapping.objects.all():
    if etm.latest_run:
        etm.state = REQUEST_STATES["OK"]
        etm.save()
    else:
        etm.state = REQUEST_STATES["INELIGIBLE"]
        etm.save()
