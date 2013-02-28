# -*- coding: utf-8 -*-
# Django settings for covscanhub (kobo hub) project.

import sys

# IF YOU NEED LATEST KOBO (FROM GIT), BE SURE TO CHANGE THIS ACCORDINGLY
sys.path.insert(0, '/home/ttomecek/dev/kobo/')

import os
import kobo

#print 'You are using kobo from %s' % kobo.__file__

# Definition of PROJECT_DIR, just for convenience:
# you can use it instead of specifying the full path
PROJECT_DIR = os.path.dirname(__file__)

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
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '$e9r6h6n@@zw)g@_6vkiug_ys0pv)tn(2x4e@zgkaany8qau8@'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
#        'django.template.loaders.eggs.Loader',
    )),
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'kobo.django.auth.krb5.Krb5AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # kobo related middleware:
    'kobo.hub.middleware.WorkerMiddleware',
    'kobo.django.menu.middleware.MenuMiddleware',
    # require login for every view
#    'covscanhub.middleware.LoginRequiredMiddleware',
)

ROOT_URLCONF = 'covscanhub.urls'
ROOT_MENUCONF = 'covscanhub.menu'

LOGIN_URL_NAME = 'auth/krb5login'
LOGIN_EXEMPT_URLS = ('^xmlrpc/')


TEMPLATE_CONTEXT_PROCESSORS = (
    #   django.core.context_processors
    # was moved to
    #   django.contrib.auth.context_processors
    # in Django 1.2 and the old location removed in Django 1.4
    'django.contrib.auth.context_processors.auth',

    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'kobo.django.menu.context_processors.menu_context_processor',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_DIR, "templates"),
    os.path.join(os.path.dirname(kobo.__file__), "hub", "templates"),
)

INSTALLED_APPS = (
    'kobo.django.auth',   # load this app first to make sure the username length hack is applied first
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    # kobo apps:
    'kobo.django.upload',
    'kobo.hub',
    # covscan
    'covscanhub.scan',
    'covscanhub.waiving',
    'covscanhub.stats',
    'django_extensions',
    'south'
)

# override default values with custom ones from local settings
try:
    from settings_local import *
except ImportError:
    pass
