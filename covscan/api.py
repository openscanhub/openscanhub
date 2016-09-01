
import os
import xmlrpclib

import kobo
from kobo.xmlrpc import SafeCookieTransport, CookieTransport


class API(object):
    """
    docs how to use this
    """
    def __init__(self, *args, **kwargs):
        self.hub_url = "http://localhost:8000/xmlrpc/kerbauth/"
        config_env = "COVSCAN_CONFIG_FILE"
        config_default = "/etc/covscan/covscan.conf"
        config_file = os.environ.get(config_env, config_default)
        conf = kobo.conf.PyConfigParser()
        conf.load_from_file(config_file)
        self._hub = None

    @property
    def hub(self):
        if self._hub is None:
            self._hub = self.connect()
        return self._hub

    def connect(self):
        """
        Connects to XML-RPC server and return client object
        Returns client objects
        """
        # we can also use kobo.xmlrpc.retry_request_decorator, which tries to perform
        # the connection several times; likely, that's not what we want in testing
        # TransportClass = kobo.xmlrpc.retry_request_decorator(kobo.xmlrpc.SafeCookieTransport)
        if "https" in self.hub_url:
            transport = SafeCookieTransport()
        elif "http" in self.hub_url:
            transport = CookieTransport()
        else:
            raise ValueError("URL to hub has to start with http(s): %r" % self.hub_url)
        client = xmlrpclib.ServerProxy(self.hub_url, allow_none=True, transport=transport,
                                       verbose=False)
        return client

    def get_filtered_scan_list(self, target=None, base=None, state=None, username=None, release=None):
        filters = dict(nvr=target, base__nvr=base, state=state, username=username, tag__release__tag=release)
        filters = dict(filter(lambda (k, v): v is not None, filters.items()))  # removes None values from dictionary
        print filters
        print '================'
        return self.hub.errata.get_filtered_scan_list(filters)
