# -*- coding: utf-8 -*-


import sys

import covscan


class List_Mock_Configs(covscan.CovScanCommand):
    """command description"""
    enabled = True
    admin = False # admin type account required

    def options(self):
        # specify command usage
        # normalized name contains a lower-case class name with underscores converted to dashes
        self.parser.usage = "%%prog %s [options] <args>" % self.normalized_name

    def run(self, *args, **kwargs):
        # optparser output is passed via *args (args) and **kwargs (opts)
        username = kwargs.pop("username", None)
        password = kwargs.pop("password", None)

        # login to the hub
        self.set_hub(username, password)

        format = "%-50s %s"
        print >> sys.stderr, format % ("NAME", "ENABLED")
        for i in self.hub.mock_config.all():
            print format % (i["name"], i["enabled"])
