import sys

from kobo.client import HubProxy

import osh.client


class List_Mock_Configs(osh.client.OshCommand):
    """list available mock configs present on hub"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        # specify command usage
        # normalized name contains a lower-case class name with underscores converted to dashes
        self.parser.usage = f"%prog {self.normalized_name} [options] <args>"

        self.parser.add_option(
            "--hub",
            help="URL of XML-RPC interface on hub; something like \
https://$hostname/covscan/xmlrpc"
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

        print("NAME", file=sys.stderr)
        for i in self.hub.mock_config.all():
            if i["enabled"]:
                print(i["name"])
