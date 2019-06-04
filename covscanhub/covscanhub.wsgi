# -*- coding: utf-8 -*-


import os
import sys


# tweak PYTHONPATH if needed (usually if project is deployed outside site-packages)
# sys.path.append("/var/www/django")

os.environ['DJANGO_SETTINGS_MODULE'] = 'covscanhub.settings'
from django.core.wsgi import get_wsgi_application


application = get_wsgi_application()
