# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from osh.client.commands.cmd_build import Base_Build
from osh.client.commands.common import (add_dist_git_url_option,
                                        add_tarball_option)


class Mock_Build(Base_Build):
    """analyze a SRPM"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        super().options()

        # this option cannot be used for diff-build tasks
        add_tarball_option(self.parser)
        add_dist_git_url_option(self.parser)

    def prepare_task_options(self, args, kwargs):
        # Check if exactly one of SRPM, NVR, or dist-git URL is provided
        if sum([bool(args), bool(kwargs.get("nvr")), bool(kwargs.get("git_url"))]) != 1:
            self.parser.error("please specify either SRPM or NVR or dist-git URL")

        self._process_srpm_option(args, kwargs)

        return super().prepare_task_options(args, kwargs)

    def submit_task(self, options):
        return self.hub.scan.mock_build(options['mock_config'],
                                        options['comment'],
                                        options)
