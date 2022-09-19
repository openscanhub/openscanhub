# -*- coding: utf-8 -*-
"""
Instance-specific settings.

Devel instance
"""

import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Kamil Dudka', 'kdudka@redhat.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'covscanhub',
        'USER': 'covscanhub',
        'PASSWORD': 'velryba',
        'HOST': 'db',
        'PORT': '5432',
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)-7s %(asctime)s %(pathname)-50s:%(lineno)d %(funcName)s   %(message)s'
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
            'filename': '/var/tmp/covscanhub.log',
            'maxBytes': 10 * (1024 ** 2),  # 10 MB
            'backupCount': 14,
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        }
    },
    'loggers': {
        'covscanhub': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        # 'django.db.backends': {
        #     'handlers': ['file'],
        #     'propagate': False,
        #     'level': 'INFO',
        # },
        'kobo': {
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

# KRB_AUTH_PRINCIPAL =
# KRB_AUTH_KEYTAB =

###############################################################################
# COVSCAN SPECIFIC
###############################################################################

# Path to task logs and other files
FILES_PATH = './covscanhub'

# Files for kobo tasks with predefined structure
TASK_DIR = os.path.join(FILES_PATH, 'tasks')

# Root directory for uploaded files
UPLOAD_DIR = os.path.join(FILES_PATH, 'upload')

BZ_URL = "https://bugzilla.stage.redhat.com/xmlrpc.cgi"
BZ_API_KEY = "xxxxxx"

ET_URL = 'https://errata-web-01.host.stage.eng.bos.redhat.com'

UMB_BROKER_URLS = [
    'amqps://umb-broker01.stage.api.redhat.com:5671',
    'amqps://umb-broker02.stage.api.redhat.com:5671',
    'amqps://umb-broker03.stage.api.redhat.com:5671',
    'amqps://umb-broker04.stage.api.redhat.com:5671',
    'amqps://umb-broker05.stage.api.redhat.com:5671',
    'amqps://umb-broker06.stage.api.redhat.com:5671']

UMB_CLIENT_CERT = '/etc/covscanhub/msg-client-covscan.pem'
UMB_TOPIC_PREFIX = 'topic://VirtualTopic.eng.covscan.scan'

ALLOWED_HOSTS = ['*']
