# -*- coding: utf-8 -*-
"""
This is a config file with instance-specific settings.
Make sure it doesn't get overwritten during package installation.
Uncoment and use whatever is needed.
"""

import os


DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Tomas Tomecek', 'ttomecek@redhat.com'),
)
MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '/tmp/covscanhub/db.sqlite',                      # Or path to database file if using sqlite3.
#        'NAME': '/var/lib/covscanhub/db.sqlite',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
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

###############################################################################
# COVSCAN SPECIFIC
###############################################################################

# kobo XML-RPC API calls
# If you define additional methods, you have to list them there.
XMLRPC_METHODS = {
    # 'handler':
    'client': (
        # module with rpc methods     prefix which is added to all methods from
        #                             the module
        ('kobo.hub.xmlrpc.auth',      'auth'),
        ('kobo.hub.xmlrpc.client',    'client'),
        ('kobo.hub.xmlrpc.system',    'system'),
        ('kobo.django.upload.xmlrpc', 'upload'),
        ('covscanhub.xmlrpc.mock_config', 'mock_config'),
        ('covscanhub.xmlrpc.scan', 'scan'),
    ),
    'worker': (
        ('kobo.hub.xmlrpc.auth',      'auth'),
        ('kobo.hub.xmlrpc.system',    'system'),
        ('kobo.hub.xmlrpc.worker',    'worker'),
        ('kobo.django.upload.xmlrpc', 'upload'),
        ('kobo.hub.xmlrpc.client',    'client'),
        ('covscanhub.xmlrpc.worker',  'worker'),
    ),
    'kerbauth': (
        ('covscanhub.xmlrpc.errata', 'errata'),
        ('covscanhub.xmlrpc.test', 'test'),
        ('kobo.hub.xmlrpc.auth',      'auth'),
    ),

}

# Absolute path to task logs and other files
FILES_PATH = '/tmp/covscanhub'
#FILES_PATH = '/var/lib/covscanhub'

# Files for kobo tasks with predefined structure
TASK_DIR = os.path.join(FILES_PATH, 'tasks')

# Root directory for uploaded files
UPLOAD_DIR = os.path.join(FILES_PATH, 'upload')

BREW_HUB = 'http://brewhub.devel.redhat.com/brewhub'
ET_SCAN_PRIORITY = 20

ACTUAL_SCANNER = ('coverity', '6.5.0')

# BZ 4.2
BZ_URL = 'https://partner-bugzilla.redhat.com/xmlrpc.cgi'
# BZ 4.4 -- new RPC API
# BZ_URL = "https://bzweb01-devel.app.eng.rdu.redhat.com/xmlrpc.cgi"
# production
# BZ_URL = "https://bugzilla.redhat.com/xmlrpc.cgi"

BZ_USER = "ttomecek@redhat.com"
BZ_PSWD = "roflcopter" # not my actual passwd on live bz

VALID_TASK_LOG_EXTENSIONS = ['.log','.ini']

#if not DEBUG:
QPID_CONNECTION = {
    'broker': "qpid-stage.app.eng.bos.redhat.com",
    'address': "eso.topic",
    'mechanism': "GSSAPI",
}
#else:
#    QPID_CONNECTION = {
#        'broker': "localhost:5672",
#        'address': "amq.topic",
#        'mechanism': 'ANONYMOUS',
#    }

QPID_CONNECTION['routing_key'] = 'covscan.scan'
