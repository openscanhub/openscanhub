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

    def submit_task(self, options):
        try:
            return self.hub.scan.mock_build(options)
        except Fault as e:
            handle_perm_denied(e, self.parser)
