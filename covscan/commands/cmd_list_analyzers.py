# -*- coding: utf-8 -*-


import sys
import random

import covscan
from kobo.client import HubProxy


class List_Analyzers(covscan.CovScanCommand):
    """list available versions of static analyzers"""
    enabled = True
    admin = False # admin type account required

    def options(self):
        self.parser.usage = "%%prog %s [options] <args>" % self.normalized_name
        self.parser.epilog = "list all available static analyzers, some of them in various versions; list contains command line arguments how to enable particular analyzer (short version, e.g. '-l' for clang and long version '--analyzer clang')"
        self.parser.add_option(
            "--hub",
            help="URL of XML-RPC interface on hub; something like \
http://$hostname/covscan/xmlrpc"
        )

    def run(self, *args, **kwargs):
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

        format = "%-20s %-20s %-15s %-25s"
        columns = ("NAME", "VERSION", "SHORT OPTION", "LONG OPTION")
        print format % columns
        available_analyzers = self.hub.scan.list_analyzers()
        for i in available_analyzers:
            print format % (i["analyzer__name"], i['version'], i["cli_short_command"],
                            i["cli_long_command"])

        shuffled_list = available_analyzers[:]
        random.shuffle(shuffled_list)
        print >> sys.stderr, "\nExample of using long option: \
\"--analyzer=%s\"" \
            % (','.join([x['cli_long_command'] for x in shuffled_list[:2]]))
