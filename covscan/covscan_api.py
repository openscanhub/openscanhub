import xmlrpclib

from kobo.xmlrpc import SafeCookieTransport, CookieTransport

from covscan.utils.conf import get_config_dict


class CovscanAPI(object):
    """
    # Class should provide basic methods to work with covscan easily.
    # You just need to import API class:
    from covscan.covscan_api import CovscanAPI
    # And then create constructor with optional hub url argument, which must end with '/xmlrpc',
    # If none url is given, url is used from covscan.conf file.
    api = CovscanAPI('http://covscan-stage.app.eng.brq.redhat.com/covscanhub/xmlrpc')
    scans = api.get_filtered_scan_list(target="python-six-1.9.0-2.el7", base='python-six-1.3.0-4.el7', username="admin",
                                       state="BASE_SCANNING", release='rhel-7.2' )
    """
    def __init__(self, hub_url=None):
        conf = get_config_dict(config_env="COVSCAN_CONFIG_FILE", config_default="/etc/covscan/covscan.conf")
        if hub_url is None and (conf is None or not conf['HUB_URL'].endswith('/xmlrpc')):
            raise ValueError('Invalid hub url in config file.')
        elif hub_url is not None and not hub_url.endswith('/xmlrpc'):
            raise ValueError('Invalid hub url was given: ' + hub_url)

        self.hub_url = hub_url if hub_url is not None else conf['HUB_URL']
        self.hub_url += '/kerbauth/'
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

    def get_filtered_scan_list(self, id=None, target=None, base=None, state=None, username=None, release=None):
        """
        Filters scans according to input arguments. If some of them are not set, filter is not used on that parameter.
        @return: dictionary containing keys 'status', 'count' and 'scans' (if status is set to 'OK')
        @see get_filtered_scan_list in covscanhub.xmlrpc.errata
        """
        filters = dict(id=id, target=target, base=base, state=state, username=username, release=release)
        filters = dict(filter(lambda (k, v): v is not None, filters.items()))  # removes None values from dictionary
        return self.hub.errata.get_filtered_scan_list(filters)
