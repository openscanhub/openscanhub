# -*- coding: utf-8 -*-

"""
Script for cron that refreshes all statistics data
"""

from covscanhub.stats.service import calculate_all


def main():
    calculate_all()


if __name__ == '__main__':
    # set python path and django settings env variable
    main()