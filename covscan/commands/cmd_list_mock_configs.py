# -*- coding: utf-8 -*-


import sys

import covscan
from kobo.client import HubProxy

class List_Mock_Configs(covscan.CovScanCommand):
    """list available mock configs present on hub"""
    enabled = True
    admin = False # admin type account required

    def options(self):
        # specify command usage
        # normalized name contains a lower-case class name with underscores converted to dashes
        self.parser.usage = "%%prog %s [options] <args>" % self.normalized_name

        self.parser.add_option(
            "--hub",
            help="URL of XML-RPC interface on hub; something like \
http://$hostname/covscan/xmlrpc"
        )

    def run(self, *args, **kwargs):
        # optparser output is passed via *args (args) and **kwargs (opts)
        username = kwargs.pop("username", None)
        password = kwargs.pop("password", None)
        hub_url = kwargs.pop('hub', None)

        # login to the hub
        if hub_url is None:
            self.set_hub(username, password)
        else:
            self.hub = HubProxy(conf=self.conf,
                                AUTH_METHOD='krbv',
                                HUB_URL=hub_url)

        format = "%-50s %s"
        print >> sys.stderr, format % ("NAME", "ENABLED")
        for i in self.hub.mock_config.all():
            print format % (i["name"], i["enabled"])
