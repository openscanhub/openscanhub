#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""
Script for cron that submits actual statistical data
"""

import sys
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).parents[2]

if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

os.environ['DJANGO_SETTINGS_MODULE'] = 'covscanhub.settings'


from covscanhub.stats.service import update


def main():
    update()


if __name__ == '__main__':
    main()