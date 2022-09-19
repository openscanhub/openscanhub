# -*- coding: utf-8 -*-
"""
Instance-specific settings.

Staging instance
"""

import os

import kobo

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Kamil Dudka', 'kdudka@redhat.com'),
)

PROJECT_DIR = os.path.dirname(__file__)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'covscanhub',
        'USER': 'covscanhub',
        'PASSWORD': 'velryba',
        'HOST': 'localhost',
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
            'filename': '/var/log/covscanhub/covscanhub.log',
            'maxBytes': 10 * (1024 ** 2),  # 10 MB
            'backupCount': 14,
        },
    },
    'loggers': {
        'covscanhub': {
            'handlers': ['file'],
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

KRB_AUTH_PRINCIPAL = 'HTTP/covscan.lab.eng.brq2.redhat.com@REDHAT.COM'
KRB_AUTH_KEYTAB = '/etc/httpd/conf/httpd.keytab'

LANGUAGE_CODE = 'en-us'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/covscanhub/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/covscanhub/admin/media/'

TEMPLATE_DIRS = (
    # directories with templates
    os.path.join(PROJECT_DIR, "templates"),
    os.path.join(os.path.dirname(kobo.__file__), "hub", "templates"),
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': TEMPLATE_DIRS,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
                "django.template.context_processors.request",
                "kobo.django.menu.context_processors.menu_context_processor",
                "django.template.context_processors.static",
            ],
        },
    },
]

###############################################################################
# COVSCAN SPECIFIC
###############################################################################

# Absolute path to task logs and other files
FILES_PATH = '/var/lib/covscanhub'

# Files for kobo tasks with predefined structure
TASK_DIR = os.path.join(FILES_PATH, 'tasks')

# Root directory for uploaded files
UPLOAD_DIR = os.path.join(FILES_PATH, 'upload')

LOGIN_URL_NAME = 'auth/krb5login'
LOGIN_EXEMPT_URLS = ['.*xmlrpc/.*']

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

ALLOWED_HOSTS = ['covscan.lab.eng.brq2.redhat.com']
