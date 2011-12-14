# -*- coding: utf-8 -*-


import os

from cmd_diff_build import Diff_Build


class Mock_Build(Diff_Build):
    """analyze a SRPM"""
    enabled = True
    admin = False # admin type account required

    def submit_task(self, config, comment, options):
        return self.hub.scan.mock_build(config, comment, options)
