# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from osh.client.commands.cmd_diff_build import Diff_Build
from osh.client.commands.common import (add_dist_git_url_option,
                                        add_tarball_option)


class Mock_Build(Diff_Build):
    """analyze a SRPM"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        super().options()

        # this option cannot be used for diff-build tasks
        add_tarball_option(self.parser)
        add_dist_git_url_option(self.parser)

    def submit_task(self, options):
        return self.hub.scan.mock_build(options['mock_config'],
                                        options['comment'],
                                        options)
