#!/usr/bin/env python3
"""

This is an XML-RPC client for OSH hub


## DEPENDENCIES

    dnf install kobo*


## USAGE


### CREATE SCAN

 ./osh/hub/scripts/osh-xmlrpc-client.py --username=admin --password=admin
    --hub http://127.0.0.1:8000/xmlrpc/kerbauth/  # has to end with '/'
    create-scan
    -b python-six-1.3.0-4.el7 -t python-six-1.9.0-2.el7
    --et-scan-id=1 --release=RHEL-7.2.0 --owner=ttomecek --advisory-id=1  # these are not important


### GET SCAN STATE

bear in mind that you need to use ID which is returned by "create-scan" -- that's what errata is
using

./osh/hub/scripts/osh-xmlrpc-client.py --hub http://127.0.0.1:8000/xmlrpc/kerbauth/ get-scan-state 13


### GET FILTERED SCAN

filter scans according to optional filters, hub url is slightly changed!

./osh/hub/scripts/osh-xmlrpc-client.py --hub http://127.0.0.1:8000/xmlrpc/client/ get-filtered-scan-list \
   --target 'python-six-1.9.0-2.el7' --base 'python-six-1.3.0-4.el7' --username='admin' \
   --state-type "BASE_SCANNING" --release='rhel-7.2'



## DEBUGGING

In case you are getting 500s and there is no sensible error message, it's likely that server is
not able to execute the XML-RPC call properly, so you need to read content of the response:

File: "/usr/lib/python2.7/site-packages/kobo/xmlrpc.py"
 481       print response.read()
 482       raise xmlrpclib.ProtocolError(host + handler, response.status, response.reason, response.msg)


"""

import argparse
import datetime
import json
import logging
import sys
import xmlrpc.client

import kobo
from kobo.tback import set_except_hook
from kobo.xmlrpc import CookieTransport, SafeCookieTransport

logger = logging.getLogger('osh_api_client')
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)

xmlrpc.client.Fault.__repr__ = lambda x: "<Fault %s: %s>" % (x.faultCode, str(x.faultString))


def create_scan_cmd(options):
    c = Client(options.hub, options.username, options.password, options.verbose)
    ret = c.create_et_scan(options.base, options.target, options.advisory_id,
                           options.et_scan_id, options.owner, options.release)
    logger.info(ret)


def get_filtered_scan_list_cmd(options):
    c = Client(options.hub)
    response = c.get_filtered_scan_list(options.id, options.target, options.base, options.username,
                                        options.state_type, options.release)
    logger.info(json.dumps(response, indent=2))


def get_scan_state_cmd(options):
    c = Client(options.hub)
    response = c.get_scan_state(options.SCAN_ID[0])
    logger.info(json.dumps(response, indent=2))


def set_options():
    parser = argparse.ArgumentParser(description="CLI client for OpenScanHub XMLRPC API")

    parser.add_argument("-v", "--verbose", help="enable debug logs and verbose traceback",
                        action="store_true")
    parser.add_argument("--username", help="username for authentication")
    parser.add_argument("--password", help="password for authentication")
    parser.add_argument(
        "--hub",
        help="full URL of API endpoint, e.g. http://172.21.0.2:8000/xmlrpc/kerbauth"
    )

    subparsers = parser.add_subparsers(help='commands')

    get_filtered_scan_list_parser = subparsers.add_parser(
        'get-filtered-scan-list',
        help='get filtered scan list'
    )
    get_filtered_scan_list_parser.add_argument("--id", help="id of scan")
    get_filtered_scan_list_parser.add_argument("--target", help="nvr of package")
    get_filtered_scan_list_parser.add_argument("--base", help="package base")
    get_filtered_scan_list_parser.add_argument("--username", help="name of owner")
    get_filtered_scan_list_parser.add_argument("--state-type", help="state of tasks")
    get_filtered_scan_list_parser.add_argument("--release", help="release name")
    get_filtered_scan_list_parser.set_defaults(func=get_filtered_scan_list_cmd)

    get_scan_state_parser = subparsers.add_parser(
        'get-scan-state',
        help='get state of a scan'
    )
    get_scan_state_parser.add_argument("SCAN_ID", help="numeric ID of a scan", nargs=1)
    get_scan_state_parser.set_defaults(func=get_scan_state_cmd)

    create_scan_parser = subparsers.add_parser(
        'create-scan',
        help='create scan, uses same endpoint as Errata Tool'
    )
    create_scan_parser.set_defaults(func=create_scan_cmd)
    create_scan_parser.add_argument("-b", "--base", help="nvr of base package to scan")
    create_scan_parser.add_argument("-t", "--target", help="nvr of target package to scan",)
    create_scan_parser.add_argument("--et-scan-id", help="database ID of run in ET")
    create_scan_parser.add_argument("--release", help="release ID")
    create_scan_parser.add_argument("--advisory-id", help="ID of advisory")
    create_scan_parser.add_argument("--owner", help="package owner")

    args = parser.parse_args()

    return parser, args


class Client:
    """
    client of XML-RPC service
    """

    def __init__(self, hub_url, username=None, password=None, verbose=False):
        self.hub_url = hub_url
        self.username = username
        self.password = password
        self.verbose = verbose
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
            raise ValueError("URL to hub has to start with http(s): " + self.hub_url)
        logger.info("connecting to %s", self.hub_url)
        client = xmlrpc.client.ServerProxy(self.hub_url, allow_none=True, transport=transport, verbose=self.verbose)
        return client

    def get_task_info(self, task_id):
        """
        executes task_info RPC call
        def task_info(request, task_id, flat=False):
        """
        logger.debug("get task info: %s", task_id)
        return self.hub.client.task_info(task_id)

    def get_scan_state(self, scan_id):
        """
        Call xmlrpc function get_scan_state
        """
        logger.debug("get scan state: %s", scan_id)
        return self.hub.errata.get_scan_state(scan_id)

    def get_filtered_scan_list(self, id=None, target=None, base=None, username=None, state=None, release=None):
        """
        Call xmlrpc function get_filtered_scan_list.
        Api has 'owner' parameter, but to be compatible with other functions 'username' is used.
        """
        filters = dict(id=id, target=target, base=base, state=state, owner=username, release=release)
        filters = {k: v for k, v in filters.items() if v is not None}  # removes None values from dictionary
        return str(self.hub.scan.get_filtered_scan_list(filters))

    def login(self):
        """
        Perform login via username/password if the credentials were provided
        """
        if self.username and self.password:
            logger.info("performing username/password login")
            self.hub.auth.login_password(self.username, self.password)

    def create_et_scan(self, base, target, advisory_id, et_id, owner, release):
        """
        Create scan, uses same method as Errata Tool
        """
        self.login()

        scan_args = {
            'package_owner': owner,
            'base': base,
            'target': target,
            'id': et_id,
            'errata_id': advisory_id,
            'rhel_version': release,
            'release': release,
        }
        return self.hub.errata.create_errata_diff_scan(scan_args)


def main():
    parser, args = set_options()
    logger.debug('You are using kobo from %s', kobo.__file__)

    verbose = args.verbose

    if verbose:
        # verbose tracebacks
        set_except_hook()

    if not args.hub.endswith("/"):
        raise ValueError("Hub URL has to end with slash (django weirdness).")

    before = datetime.datetime.now()
    try:
        args.func(args)
    except AttributeError:
        if hasattr(args, 'func'):
            raise
        parser.print_help()
        return 2
    except KeyboardInterrupt:
        print("Quitting on user request.")
        return 1
    # otherwise raise the exception

    delta = datetime.datetime.now() - before
    logger.debug('Execution took %d.%d s.', delta.seconds, delta.microseconds)
    logger.info("Everything is fine.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
