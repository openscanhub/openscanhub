# -*- coding: utf-8 -*-


import sys
import random

import covscan
from kobo.client import HubProxy


class List_Profiles(covscan.CovScanCommand):
    """list available versions of static analyzers"""
    enabled = True
    admin = False # admin type account required

    def options(self):
        self.parser.usage = "%%prog %s" % self.normalized_name
        self.parser.epilog = "List of predifned scanning profiles. " \
                             "These profiles serve as predefined scanning environments. " \
                             "One scanning profile could be for C, another for python, shell..."


    def run(self, *args, **kwargs):
        username = kwargs.pop("username", None)
        password = kwargs.pop("password", None)

        # login to the hub
        self.set_hub(username, password)

        format = "%-20s %s"
        columns = ("NAME", "DESCRIPTION")
        print format % columns
        available_analyzers = self.hub.scan.list_profiles()
        for i in available_analyzers:
            print format % (i["name"], i['description'])
