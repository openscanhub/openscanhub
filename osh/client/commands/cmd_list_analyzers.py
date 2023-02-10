import random
import sys

from kobo.client import HubProxy

import osh.client


class List_Analyzers(osh.client.CovScanCommand):
    """list available versions of static analyzers"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        self.parser.usage = f"%prog {self.normalized_name} [options] <args>"
        self.parser.epilog = "list all available static analyzers, some of them in various versions;" + " list contains command line arguments how to enable particular analyzer " + "(e.g. '--analyzer clang' for clang)"
        self.parser.add_option(
            "--hub",
            help="URL of XML-RPC interface on hub; something like \
https://$hostname/covscan/xmlrpc"
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

        format = "%-20s %-20s %-25s"
        columns = ("NAME", "VERSION", "ANALYZER_ID")
        print(format % columns)
        available_analyzers = self.hub.scan.list_analyzers()
        for i in available_analyzers:
            print(format % (i["analyzer__name"], i['version'], i["cli_long_command"]))

        shuffled_list = available_analyzers[:]
        random.shuffle(shuffled_list)
        print("\nExample of usage: \
\"--analyzer=%s\"" % (','.join([x['cli_long_command'] for x in shuffled_list[:2]])), file=sys.stderr)
