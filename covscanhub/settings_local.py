# -*- coding: utf-8 -*-


"""
This is a config file with instance-specific settings.
Make sure it doesn't get overwritten during package installation.
Uncoment and use whatever is needed.
"""


DEBUG = True
TEMPLATE_DEBUG = DEBUG

#ADMINS = (
#    # ('Your Name', 'your_email@domain.com'),
#)
#MANAGERS = ADMINS

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
#TIME_ZONE = 'America/New_York'
#LANGUAGE_CODE = 'en-us'
#USE_I18N = False
