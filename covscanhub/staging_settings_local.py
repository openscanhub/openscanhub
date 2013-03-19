# -*- coding: utf-8 -*-
"""
Instance-specific settings.

Staging instance
"""

import sys

KOBO_DIR = '/home/brq/ttomecek/dev/kobo'

if KOBO_DIR not in sys.path:
    sys.path.append(KOBO_DIR)

import kobo
import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Tomas Tomecek', 'ttomecek@redhat.com'),
)

PROJECT_DIR = os.path.dirname(__file__)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/var/covscanhub/db.sqlite',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s\t%(filename)s:%(lineno)s \
%(funcName)s\t%(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': '/var/log/covscanhub.log',
            'maxBytes': 10 * (1024 ** 2),
            'backupCount': 7,
        },
    },
    'loggers': {
        'covscanhub': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        }
    }
}

# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = 'Europe/Bratislava'

KRB_AUTH_PRINCIPAL = 'HTTP/uqtm.lab.eng.brq.redhat.com@REDHAT.COM'
KRB_AUTH_KEYTAB = '/etc/httpd/conf/httpd.keytab'

LANGUAGE_CODE = 'en-us'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/covscan/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/covscan/admin/media/'

TEMPLATE_DIRS = (
    # directories with templates
    os.path.join(PROJECT_DIR, "templates"),
    os.path.join(os.path.dirname(kobo.__file__), "hub", "templates"),
)

###############################################################################
# COVSCAN SPECIFIC
###############################################################################

# Absolute path to task logs and other files
FILES_PATH = '/var/lib/covscanhub'

# Files for kobo tasks with predefined structure
TASK_DIR = os.path.join(FILES_PATH, 'tasks')

# Root directory for uploaded files
UPLOAD_DIR = os.path.join(FILES_PATH, 'upload')

ACTUAL_SCANNER = ('coverity', '6.5.0')

LOGIN_URL_NAME = 'auth/krb5login'
LOGIN_EXEMPT_URLS = ['.*xmlrpc/.*']

# BZ 4.2
BZ_URL = 'https://partner-bugzilla.redhat.com/xmlrpc.cgi'
# BZ 4.4 -- new RPC API
# BZ_URL = "https://bzweb01-devel.app.eng.rdu.redhat.com/xmlrpc.cgi"
# production
# BZ_URL = "https://bugzilla.redhat.com/xmlrpc.cgi"

BZ_USER = "ttomecek@redhat.com"
BZ_PSWD = "roflcopter" # not my actual passwd on live bz

QPID_CONNECTION = {
    'broker': "qpid-stage.app.eng.bos.redhat.com",
    'address': "eso.topic",
    'mechanism': "GSSAPI",
}

QPID_CONNECTION['routing_key'] = 'covscan.scan'
