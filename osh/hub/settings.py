# -*- coding: utf-8 -*-
# Django global settings for covscanhub

# DEBUG = True

from __future__ import absolute_import

import os

import kobo

# Definition of PROJECT_DIR, just for convenience:
# you can use it instead of specifying the full path
PROJECT_DIR = os.path.dirname(__file__)

URL_PREFIX = "/covscanhub"

# file to read the real SECRET_KEY from
SECRET_KEY_FILE = "/var/lib/osh/hub/secret_key"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_DIR, "media/")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/covscanhub/media/'

STATIC_URL = URL_PREFIX + '/static/'

STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')

STATICFILES_DIRS = (
    os.path.join(PROJECT_DIR, "media"),
)

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

ROOT_URLCONF = 'osh.hub.urls'
ROOT_MENUCONF = 'osh.hub.menu'

# dummy secret key
# (will be overridden by the content of SECRET_KEY_FILE if available)
SECRET_KEY = 'x' * 50

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
        # 'django.template.loaders.eggs.Loader',
    )),
)

AUTHENTICATION_BACKENDS = (
    'kobo.django.auth.krb5.Krb5RemoteUserBackend',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_USER_MODEL = 'kobo_auth.User'

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'kobo.django.auth.middleware.LimitedRemoteUserMiddleware',
    'kobo.hub.middleware.WorkerMiddleware',
    'kobo.django.menu.middleware.MenuMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

INTERNAL_IPS = ('127.0.0.1',)


LOGIN_URL_NAME = 'auth/krb5login'
LOGIN_EXEMPT_URLS = ('.*xmlrpc/.*')

INSTALLED_APPS = (
    'django.contrib.auth',
    'kobo.django.auth.apps.AuthConfig',

    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.staticfiles',

    # nice numbers and dates
    'django.contrib.humanize',

    # kobo apps:
    'kobo.django.upload',
    'kobo.django.xmlrpc',
    'kobo.hub',

    # covscan
    'osh.hub.errata',
    'osh.hub.scan',
    'osh.hub.waiving',
    'osh.hub.stats',

    # better ./manage.py shell
    # 'django_extensions',
    'debug_toolbar',
)

DEBUG_TOOLBAR_PATCH_SETTINGS = False
DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]

# pagination by default was removed in kobo-0.4.2~9 (use this to re-enable it)
PAGINATE_BY = 50

###############################################################################
# COVSCAN SPECIFIC
###############################################################################

# kobo XML-RPC API calls
# If you define additional methods, you have to list them there.
XMLRPC_METHODS = {
    # 'handler': (/xmlrpc/<handler>)
    'client': (
        # module with rpc methods     prefix which is added to all methods from
        #                             the module
        ('kobo.hub.xmlrpc.auth', 'auth'),
        ('kobo.hub.xmlrpc.client', 'client'),
        ('kobo.hub.xmlrpc.system', 'system'),
        ('kobo.django.upload.xmlrpc', 'upload'),
        ('osh.hub.cs_xmlrpc.mock_config', 'mock_config'),
        ('osh.hub.cs_xmlrpc.scan', 'scan'),
    ),
    'worker': (
        ('kobo.hub.xmlrpc.auth', 'auth'),
        ('kobo.hub.xmlrpc.system', 'system'),
        ('kobo.hub.xmlrpc.worker', 'worker'),
        ('kobo.django.upload.xmlrpc', 'upload'),
        ('kobo.hub.xmlrpc.client', 'client'),
        ('osh.hub.cs_xmlrpc.worker', 'worker'),
    ),
    'kerbauth': (
        ('osh.hub.cs_xmlrpc.errata', 'errata'),
        ('osh.hub.cs_xmlrpc.test', 'test'),
        ('kobo.hub.xmlrpc.auth', 'auth'),
    ),

}

LOGIN_URL_NAME = 'auth/krb5login'
LOGIN_EXEMPT_URLS = ['.*xmlrpc/.*']

BREW_URL = 'https://brewhub.engineering.redhat.com/brewhub'
BREW_BIN_NAME = 'brew'
KOJI_URL = 'https://koji.fedoraproject.org/kojihub'
KOJI_BIN_NAME = 'koji'
ET_SCAN_PRIORITY = 20

VALID_TASK_LOG_EXTENSIONS = ['.log', '.ini', '.err', '.out', '.js', '.txt']

# override default values with custom ones from local settings
try:
    from .settings_local import *  # noqa
except ImportError:
    pass

# read the real SECRET_KEY from SECRET_KEY_FILE if availble
try:
    with open(SECRET_KEY_FILE, 'r') as f:
        key = f.readline()
        SECRET_KEY = key.strip()
except OSError:
    pass