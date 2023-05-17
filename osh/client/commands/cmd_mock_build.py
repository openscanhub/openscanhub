# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from xmlrpc.client import Fault

from osh.client.commands.cmd_diff_build import Diff_Build
from osh.client.commands.common import add_tarball_option
from osh.client.commands.shortcuts import handle_perm_denied


class Mock_Build(Diff_Build):
    """analyze a SRPM"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        super().options()

        # this option cannot be used for diff-build tasks
        add_tarball_option(self.parser)

    def submit_task(self, config, comment, options):
        try:
            return self.hub.scan.mock_build(config, comment, options)
        except Fault as e:
            handle_perm_denied(e, self.parser)
