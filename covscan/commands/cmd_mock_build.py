# -*- coding: utf-8 -*-


from shortcuts import handle_perm_denied
from xmlrpclib import Fault
from cmd_diff_build import Diff_Build
from covscan.commands.common import add_tarball_option


class Mock_Build(Diff_Build):
    """analyze a SRPM"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        Diff_Build.options(self)

        # this option cannot be used for diff-build tasks
        add_tarball_option(self.parser)

    def submit_task(self, config, comment, options):
        try:
            return self.hub.scan.mock_build(config, comment, options)
        except Fault, e:
            handle_perm_denied(e, self.parser)
