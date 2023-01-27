# -*- coding: utf-8 -*-

from __future__ import absolute_import

from six.moves.xmlrpc_client import Fault

from .cmd_diff_build import Diff_Build
from .common import add_tarball_option
from .shortcuts import handle_perm_denied


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
        except Fault as e:
            handle_perm_denied(e, self.parser)
