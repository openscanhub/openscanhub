# -*- coding: utf-8 -*-
# Django global settings for covscanhub

import os

# Definition of PROJECT_DIR, just for convenience:
# you can use it instead of specifying the full path
PROJECT_DIR = os.path.dirname(__file__)

URL_PREFIX = ""

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

STATIC_URL = URL_PREFIX + '/static/'

STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')

STATICFILES_DIRS = (
    os.path.join(PROJECT_DIR, "media"),
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '$e9r6h6n@@zw)g@_6vkiug_ys0pv)tn(2x4e@zgkaany8qau8@'

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

AUTH_USER_MODEL = 'auth.LongnameUser'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'kobo.django.auth.middleware.LimitedRemoteUserMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',

    # kobo related middleware:
    'kobo.hub.middleware.WorkerMiddleware',
    'kobo.django.menu.middleware.MenuMiddleware',

    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

INTERNAL_IPS = ('127.0.0.1',)

ROOT_URLCONF = 'covscanhub.urls'
ROOT_MENUCONF = 'covscanhub.menu'

LOGIN_URL_NAME = 'auth/krb5login'
LOGIN_EXEMPT_URLS = ('.*xmlrpc/.*')

TEMPLATE_CONTEXT_PROCESSORS = (
    #   django.core.context_processors
    # was moved to
    #   django.contrib.auth.context_processors
    # in Django 1.2 and the old location removed in Django 1.4
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'kobo.django.menu.context_processors.menu_context_processor',
    "django.core.context_processors.static",
)

INSTALLED_APPS = (
    'kobo.django.auth',

    #'django.contrib.auth',

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
    'kobo.hub',

    # covscan
    'covscanhub.scan',
    'covscanhub.waiving',
    'covscanhub.stats',

    # better ./manage.py shell
    'django_extensions',
    'debug_toolbar',

    # migrations
    #'south'
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
        ('kobo.hub.xmlrpc.auth',          'auth'),
        ('kobo.hub.xmlrpc.client',        'client'),
        ('kobo.hub.xmlrpc.system',        'system'),
        ('kobo.django.upload.xmlrpc',     'upload'),
        ('covscanhub.xmlrpc.mock_config', 'mock_config'),
        ('covscanhub.xmlrpc.scan',        'scan'),
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
        ('covscanhub.xmlrpc.test',   'test'),
        ('kobo.hub.xmlrpc.auth',     'auth'),
    ),

}

BREW_HUB = 'http://brewhub.devel.redhat.com/brewhub'
ET_SCAN_PRIORITY = 20

VALID_TASK_LOG_EXTENSIONS = ['.log', '.ini', '.err', '.out', '.js', '.txt']

# override default values with custom ones from local settings
try:
    from settings_local import *
except ImportError:
    pass
