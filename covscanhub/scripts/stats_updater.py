#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""
Script for cron that submits actual statistical data
"""

import sys
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname
    (os.path.abspath(__file__))))   

if PROJECT_DIR not in sys.path:
    print '%s is not on sys.path' % PROJECT_DIR 
    sys.path.append(PROJECT_DIR)

os.environ['DJANGO_SETTINGS_MODULE'] = 'covscanhub.settings'


from covscanhub.stats.service import update


def main():
    update()


if __name__ == '__main__':
    main()