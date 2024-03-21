# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import os


def get_secret(name, directory):
    try:
        with open(os.path.join(directory, name)) as f:
            return f.read().strip()
    except OSError:
        return None
