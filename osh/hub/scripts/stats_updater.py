#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""
Script for cron that submits actual statistical data
"""

import os
import sys
from pathlib import Path

from osh.hub.stats.service import update

PROJECT_DIR = Path(__file__).parents[2]

if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

os.environ['DJANGO_SETTINGS_MODULE'] = 'osh.hub.settings'


def main():
    update()


if __name__ == '__main__':
    main()
