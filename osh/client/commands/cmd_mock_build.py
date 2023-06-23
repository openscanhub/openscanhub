# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from osh.client.commands.cmd_diff_build import Diff_Build


class Mock_Build(Diff_Build):
    """analyze a SRPM"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        super().options()

        # this option cannot be used for diff-build tasks
        self.parser.add_option(
            "--tarball-build-script",
            dest="tarball_build_script",
            action="store",
            help="With this option osh-cli accepts path to tarball specified via first argument and "
                 "then the tarball will be scanned. "
                 "This option sets command which should build the package, usually this should be just "
                 "\"make\", in case of packages which doesn't need to be built, just pass \"true\".",
        )

    def submit_task(self, options):
        return self.hub.scan.mock_build(options['mock_config'],
                                        options['comment'],
                                        options)
