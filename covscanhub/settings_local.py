# -*- coding: utf-8 -*-
"""
Instance-specific settings.

Devel instance
"""

import sys

KOBO_DIR = '/home/ttomecek/dev/kobo'
if KOBO_DIR not in sys.path:
    sys.path.insert(0, KOBO_DIR)

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
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
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
            'maxBytes': 10 * (1024 ** 2),  # 10 MB
            'backupCount': 14,
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

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Prague'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin/media/'

TEMPLATE_DIRS = (
    # directories with templates
    os.path.join(PROJECT_DIR, "templates"),
    os.path.join(os.path.dirname(kobo.__file__), "hub", "templates"),
)

###############################################################################
# COVSCAN SPECIFIC
###############################################################################

# Absolute path to task logs and other files
FILES_PATH = '/var/covscanhub'

# Files for kobo tasks with predefined structure
TASK_DIR = os.path.join(FILES_PATH, 'tasks')

# Root directory for uploaded files
UPLOAD_DIR = os.path.join(FILES_PATH, 'upload')

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

#if not DEBUG:
QPID_CONNECTION = {
    'broker': "qpid-stage.app.eng.bos.redhat.com",
    'address': "eso.topic",
    'mechanism': "GSSAPI",
}

QPID_CONNECTION['routing_key'] = 'covscan.scan'

#else:
#    QPID_CONNECTION = {
#        'broker': "localhost:5672",
#        'address': "amq.topic",
#        'mechanism': 'ANONYMOUS',
#    }


