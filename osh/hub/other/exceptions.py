# -*- coding: utf-8 -*-


class BrewException(Exception):
    pass


class ScanException(Exception):
    """
    Something went wrong with scanning
    """


class PackageNotEligibleException(ScanException):
    """
    Package is not eligible for scanning
    """


class PackageBlacklistedException(ScanException):
    """
    Package is not eligible for scanning
    """
