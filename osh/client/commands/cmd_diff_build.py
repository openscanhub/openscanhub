# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from osh.client.commands.cmd_build import Base_Build


class Diff_Build(Base_Build):
    """analyze a SRPM without and with patches, return diff"""
    enabled = True
    admin = False  # admin type account required

    def prepare_task_options(self, args, kwargs):
        if bool(args) == bool(kwargs.get("nvr")):
            self.parser.error("please specify either SRPM or NVR")

        self._process_srpm_option(args, kwargs)

        return super().prepare_task_options(args, kwargs)

    def submit_task(self, options):
        return self.hub.scan.diff_build(options['mock_config'],
                                        options['comment'],
                                        options)
