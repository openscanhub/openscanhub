import xmlrpclib

from kobo.xmlrpc import SafeCookieTransport, CookieTransport

from covscan.utils.conf import get_config_dict


class Api(object):
    """
    Class should provide basic methods to work with covscan easily.
    """
    def __init__(self):
        conf = get_config_dict(config_env="COVSCAN_CONFIG_FILE", config_default="/etc/covscan/covscan.conf")
        if conf is None or not conf['HUB_URL'].endswith('/xmlrpc'):
            raise ValueError('Invalid hub url in config file.')
        self.hub_url = conf['HUB_URL'] + '/kerbauth/'
        self._hub = None

    @property
    def hub(self):
        if self._hub is None:
            self._hub = self.connect()
        return self._hub

    def connect(self):
        """
        Connects to XML-RPC server.
        @return: client object
        """

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
        """
        Filters scans according to input arguments.
        @return: dictionary containing keys 'status', 'count' and 'scans' (if status is set to 'OK')
        @see get_filtered_scan_list in covscanhub.xmlrpc.errata
        """
        filters = dict(nvr=target, base__nvr=base, state=state, username=username, tag__release__tag=release)
        filters = dict(filter(lambda (k, v): v is not None, filters.items()))  # removes None values from dictionary
        return self.hub.errata.get_filtered_scan_list(filters)
