#!/usr/bin/python -tt
"""

This class should provide basic methods to work with covscan easily.


## DEPENDENCIES

    yum install kobo*


## USAGE

You just need to import API class:

    from covscan.covscan_api import CovscanAPI

And then create constructor with optional hub url argument, which must end with '/xmlrpc':

    api = CovscanAPI('https://covscan-stage.lab.eng.brq2.redhat.com/covscanhub/xmlrpc')

Finally, use method which you like according to its doc, f.e. get_filtered_scan_list with optional args:

    scans = api.get_filtered_scan_list(id=3, target="python-six-1.9.0-2.el7", base='python-six-1.3.0-4.el7',
                                       owner="admin", state="BASE_SCANNING", release='rhel-7.2' )

If none url is given, url is used from HUB_URL constant from covscan config file.

To avoid sending too much data through xmlrpc, there is a default limit which sets maxcimum number of sent scans.
If limit is exceeded, only limited amount of scans is sent. Scans are sorted by its submission date, from newest to
oldest. This limit is also configurable in config file as FILTER_SCAN_LIMIT constant.

"""

import xmlrpclib

from covscan.utils.conf import get_config_dict
from covscanhub.other.constants import DEFAULT_SCAN_LIMIT


class CovscanAPI(object):

    def __init__(self, hub_url=None):
        conf = get_config_dict(config_env="COVSCAN_CONFIG_FILE", config_default="/etc/covscan/covscan.conf")
        if hub_url is None and (conf is None or not conf['HUB_URL'].endswith('/xmlrpc')):
            raise ValueError('Invalid hub url in config file.')
        elif hub_url is not None and not hub_url.endswith('/xmlrpc'):
            raise ValueError('Invalid hub url was given: ' + hub_url)

        if 'FILTER_SCAN_LIMIT' in conf:
            self.filter_scan_limit = conf['FILTER_SCAN_LIMIT']
        else :
            self.filter_scan_limit = DEFAULT_SCAN_LIMIT

        self.hub_url = hub_url if hub_url is not None else conf['HUB_URL']
        self.hub_url += '/client/'
        self._hub = None

    @property
    def hub(self):
        if self._hub is None:
            self._hub = self.__connect()
        return self._hub

    def __connect(self):
        """
        Connects to XML-RPC server.
        @return: client object
        """

        client = xmlrpclib.ServerProxy(self.hub_url, allow_none=True, verbose=False)
        return client

    def get_filtered_scan_list(self, id=None, target=None, base=None, state=None, owner=None, release=None):
        """
        Filters scans according to input arguments. If some of them are not set, filter is not used on that parameter.
        Scans are sorted by its submission date, from newest to oldest.

        Pretty print of output is shown below:

            {'count': 1,
             'scans': [{'base_id': 4,                        # id of the base, None if it does not exist
                        'base_target': 'python-six-1.3.0-4.el7',
                                                             # full name of the base, None if it does not exist
                        'date_last_accessed': <DateTime '20160818T13:10:04' at 7f24282e73f8>,
                                                             # DateTime object, when the scan was last time accessed
                        'date_submitted': <DateTime '20160818T13:10:04' at 7f24282e7440>,
                                                             # DateTime object, when the scan was submitted
                        'id': 3,                             # scan id
                        'is_enabled': True,                  # True if package is enabled
                        'package_is_blocked': False,         # True if package is blocked
                        'package_is_eligible': True,         # True if package is eligible
                        'package_name': 'python-six',        # package name (without version, release)
                        'release': 'rhel-7.2',               # release of the scan
                        'scan_type': 3,                      # scan number according to SCAN_TYPES (errata, rebase, ..)
                        'state': 7,                          # number of scan according to SCAN_STATES
                        'tag_name': 'RHEL-7.2',              # tag name, usually release with capitals
                        'target': 'python-six-1.9.0-2.el7',  # full target name
                        'owner_email': 'devnull@redhat.com', # owner email
                        'owner_name': 'admin'}],             # owner name
             'status': 'OK'}

        @return: dictionary containing keys 'status', 'count' and 'scans' (if status is set to 'OK'); if status is set
                 to 'ERROR', 'message' key containing error output is there instead
        @see get_filtered_scan_list in covscanhub.xmlrpc.scan
        """

        filters = dict(id=id, target=target, base=base, state=state, owner=owner, release=release)
        filters = dict(filter(lambda (k, v): v is not None, filters.items()))  # removes None values from dictionary
        return self.hub.scan.get_filtered_scan_list(filters, self.filter_scan_limit)
