#!/usr/bin/env python3

"""
Script for cron that submits actual statistical data
"""

import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('osh-stats')

os.environ['DJANGO_SETTINGS_MODULE'] = 'osh.hub.settings'


def main():
    import django
    django.setup()

    from osh.hub.stats.service import update

    update()


if __name__ == '__main__':
    main()
