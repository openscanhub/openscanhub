# -*- coding: utf-8 -*-

"""
    Module that retrieves statistcs data. It would be for the best if the
    information would be stored in own table, something like:

    STAT_KEY            STAT_VALUE             COMMENT
    ===========================================================================
    TOTAL_SCANS         999                    'Total number of scans'
    TOTAL_DEFECTS       9123                   'Total number of found defects'
    etc.

    and this table would be reloaded once a day.

    Create structure and prefill DB with it (scripts.db):
        [
            (STAT_KEY, COMMENT),
            (STAT_KEY2, COMMENT2),
            ...
        ]
"""

#######
# SCANS
#######


def get_total_scans():
    """
        Return total number of all scans
    """


def get_scans_by_release():
    """
        Return total number of scans by release (RHEL-6.4, 7.1, etc.)
    """

#####
# LOC
#####


def get_total_lines():
    """
        Show total number of LoC scanned
    """


def get_lines_by_release():
    """
        Show total number of LoC scanned by RHEL release
    """

#########
# DEFECTS
#########


def get_total_defects():
    """
        Return total number of found defects
    """


def get_defects_by_release():
    """
        Return total number of found defects by release
    """


def get_total_fixed_defects():
    """
        Return total number of found defects
    """


def get_fixed_defects_by_release():
    """
        Return total number of found defects by release
    """


def get_total_new_defects():
    """
        Return total number of found defects
    """


def get_new_defects_by_release():
    """
        Return total number of found defects by release
    """

#########
# WAIVERS
#########


def get_total_waivers_submitted():
    """
        Return total number of waivers submitted
    """


def get_waivers_submitted_by_release():
    """
        Return total number of waivers submitted by release
    """


def get_


