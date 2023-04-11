class BrewException(Exception):
    pass


class ScanException(Exception):
    """
    Something went wrong with scanning
    """


class PackageBlacklistedException(ScanException):
    """
    Package is not eligible for scanning
    """
