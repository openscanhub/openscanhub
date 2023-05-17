# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

class ScanException(Exception):
    """
    Something went wrong with scanning
    """


class PackageBlockedException(ScanException):
    """
    Package is not eligible for scanning
    """
