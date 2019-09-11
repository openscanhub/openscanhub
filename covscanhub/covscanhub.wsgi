# -*- coding: utf-8 -*-


from __future__ import absolute_import
import os
import sys


# tweak PYTHONPATH if needed (usually if project is deployed outside site-packages)
# sys.path.append("/var/www/django")

os.environ['DJANGO_SETTINGS_MODULE'] = 'covscanhub.settings'
import django.core.handlers.wsgi


application = django.core.handlers.wsgi.WSGIHandler()
