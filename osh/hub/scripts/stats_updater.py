#!/usr/bin/env python3

"""
Script for cron that submits actual statistical data
"""

import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'osh.hub.settings'


def main():
    import django
    django.setup()

    from osh.hub.stats.service import update

    update()


if __name__ == '__main__':
    main()
