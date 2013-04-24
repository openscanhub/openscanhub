#!/usr/bin/python -tt
"""
XML-RPC call against covscan tool with kerberos authentication.
You have to have kobo module (yum install kobo) to run this example.

You have to have kobo module to successfully run this code.

This module is present in Fedora repositories and in EPEL:

    yum install kobo*
"""
import sys

KOBO_DIR = '/home/ttomecek/dev/kobo'

if KOBO_DIR not in sys.path:
    sys.path.insert(0, KOBO_DIR)

from kobo.tback import Traceback, set_except_hook
#print sys.excepthook
set_except_hook()
#print sys.excepthook

import kobo
import xmlrpclib
import kobo.xmlrpc
import pdb
import urlparse
import base64
import random
import datetime

from optparse import OptionParser


def set_options():
    parser = OptionParser()
    parser.add_option("-l", "--localhost", help="target hub is localhost",
                      action="store_true", dest="hub_local", default=False)
    parser.add_option("-s", "--staging", help="target hub is staging",
                      action="store_true", dest="hub_staging", default=False)
    parser.add_option("-p", "--production", help="target hub is production",
                      action="store_true", dest="hub_prod", default=False)
    parser.add_option("-i", "--init", help="create scan requests",
                      action="store_true", dest="init", default=False)
    parser.add_option("-b", "--base", action="store", type="string",
                      dest="base",
                      help="nvr of base package to scan")
    parser.add_option("-t", "--target", action="store", type="string",
                      dest="target",
                      help="nvr of target package to scan",)
    parser.add_option("-f", "--file", help="create base scans from this file",
                      action="store", type="string", dest="file")
    parser.add_option("-T", "--tag", help="name of tag for mass prescan",
                      action="store", type="string", dest="tag_name")
    parser.add_option("-m", "--send-message", help="send random message to qpid broker",
                      action="store_true", dest="messaging")

    parser.add_option("-S", "--get-state", help="get scan's state",
                      action="store", type="int", dest="scan_state")

    parser.add_option("--info", help="get task's info",
                      action="store", type="int", dest="task_info")

    (options, args) = parser.parse_args()

    return parser, options, args


def connect(rpc_url):
    """
    Connects to XML-RPC server and return client object
    Returns client objects
    """
    #SSL transport
    #TransportClass = kobo.xmlrpc.retry_request_decorator(
    #    kobo.xmlrpc.SafeCookieTransport)
    TransportClass = kobo.xmlrpc.retry_request_decorator(
        kobo.xmlrpc.CookieTransport)
    transport = TransportClass()

    client = xmlrpclib.ServerProxy(rpc_url, allow_none=True,
                                   transport=transport)
    return client


def call_task_info(client, task_id):
    """
    executes task_info RPC call
    def task_info(request, task_id, flat=False):
    """
    result = client.client.task_info(task_id)
    for key, value in result.iteritems():
        print "%s = %s" % (key, value)


def call_task_url(client, task_id):
    """
    executes task_url RPC call
    def task_url(request, task_id):
    """
    return client.client.task_url(task_id)


def call_resubmit_task(client, task_id):
    """
    executes resubmit_task RPC call
    requires login
    def resubmit_task(request, task_id):
    """
    return client.client.resubmit_task(task_id)

def call_errata_version_task(client, kwargs):
    """
    Call function scan.create_version_diff_task
    """
    return client.errata.create_errata_diff_scan(kwargs)

def call_version_task(client, kwargs):
    """
    Call function scan.create_version_diff_task
    """
    return client.scan.create_user_diff_task(kwargs)


def call_get_scan_state(client, scan_id):
    """
    Call xmlrpc function get_scan_state
    """
    return client.errata.get_scan_state(scan_id)

def call_send_message(client):
    """
    """
    return client.test.send_message()

def login(rpc_url):
    """
    authenticates against RPC server using kerberos with
    locally initialized ticket
    """
    def get_server_principal(service=None, realm=None):
        """Convert hub url to kerberos principal."""
        hostname = urlparse.urlparse(rpc_url)[1]
        # remove port from hostname
        hostname = hostname.split(":")[0]

        if realm is None:
            # guess realm: last two parts from hostname
            realm = ".".join(hostname.split(".")[-2:]).upper()
        if service is None:
            service = "HTTP"
        return (realm, '%s/%s@%s' % (service, hostname, realm))
    import krbV
    ctx = krbV.default_context()
    #print "%s ctx:" % ('=' * 20)
    #for i in dir(ctx):
    #    print "%s = %s" % (i, getattr(ctx, i))
    ccache = ctx.default_ccache()
    #print "%s ccache:" % ('=' * 20)
    #for i in dir(ccache):
    #    print "%s = %s" % (i, getattr(ccache, i))
    cprinc = ccache.principal()
    #print "%s cprinc:" % ('=' * 20)
    #print cprinc
    #pdb.set_trace()
    realm, sprinc_str = get_server_principal()
    print sprinc_str
    sprinc = krbV.Principal(name=sprinc_str, context=ctx)

    ac = krbV.AuthContext(context=ctx)
    ac.flags = krbV.KRB5_AUTH_CONTEXT_DO_SEQUENCE | \
               krbV.KRB5_AUTH_CONTEXT_DO_TIME
    ac.rcache = ctx.default_rcache()

    try:
        ac, req = ctx.mk_req(server=sprinc, client=cprinc,
                             auth_context=ac, ccache=ccache,
                             options=krbV.AP_OPTS_MUTUAL_REQUIRED)
    except krbV.Krb5Error, ex:
        print ex
        if getattr(ex, "err_code", None) == -1765328377:
            ex.message += ". Make sure you correctly set \
KRB_REALM (current value: %s)." % realm
            ex.args = (ex.err_code, ex.message)
        raise ex
    return base64.encodestring(req)


def create_et_scan(client, base, target):
    """
    Connect to RPC server, login and execute some method
    """
    #login_krbv is rpc call
    #print client.auth.login_krbv(login())
    #if '127.0.0.1' in RPC_URL or 'localhost' in RPC_URL:
    #    client.auth.login_password('ttomecek', 'tatry')

    p = random.randint(1, 100000)
    p2 = random.randint(1, 100000)
    try:
        scan_args = {
            'package_owner': 'ttomecek',
            'base': base,
            'target': target,
            'id': str(p),
            'errata_id': str(p2),
            'rhel_version': "RHEL-6.4.0",
            'release': 'RHEL-6.4.0',
        }
    except Exception:
        print "Usage:\n%prog -b <base_nvr> -t <target_nvr>"
        sys.exit(1)
    #'base': 'units-1.87-4.el6' 'nvr': 'units-1.87-7.el6',
    #print call_send_message(client)
    print call_errata_version_task(client, scan_args)

def init_scans(client):
    nvrs = [
        ('libssh2-1.2.2-7.el6', 'libssh2-1.4.2-1.el6'),
        ('wget-1.12-1.4.el6', 'wget-1.12-1.8.el6'),
        ('glibc-2.12-1.80.el6', 'glibc-2.12-1.106.el6'),
        ('btparser-0.16-3.el6', 'btparser-0.17-1.el6'),
        ('sysfsutils-2.1.0-6.1.el6', 'sysfsutils-2.1.0-7.el6'),
        ('iok-1.3.13-2.el6', 'iok-1.3.13-3.el6'),
        ('cifs-utils-4.8.1-10.el6', 'cifs-utils-4.8.1-14.el6'),
        ('systemd-191-2.fc18', 'systemd-192-1.fc18', ),
        ('systemd-191-2.fc18', 'systemd-193-1.fc18', ),
        ('systemd-191-2.fc18', 'systemd-194-1.fc18', ),
        ('systemd-191-2.fc18', 'systemd-195-2.fc18', ),
        ('systemd-191-2.fc18', 'systemd-196-1.fc19', ),
    ]
    for b in nvrs:
        scan_args = {
            'package_owner': 'ttomecek',
            'base': b[0],
            'target': b[1],
            'id': 'test_id',
            'errata_id': 'test_id2',
            'rhel_version': "RHEL-6.4.0",
            'release': 'RHEL-6.4.0',
        }
        print call_errata_version_task(client, scan_args)


def mass_prescan(client, file_path, parser, tag_name):
    try:
        fp = open(file_path, 'r')
    except IOError:
        parser.error('Cannot open specified file')
    print client.scan.create_base_scans(fp.read().splitlines(), tag_name)


if __name__ == '__main__':
    print 'You are using kobo from %s' % kobo.__file__

    parser, options, args = set_options()

    rpc_url = "http://uqtm.lab.eng.brq.redhat.com/covscan/xmlrpc/kerbauth/"
    if options.hub_local:
        rpc_url = "http://127.0.0.1:8000/xmlrpc/kerbauth/"
    elif options.hub_prod:
        #rpc_url = "https://releng-test1.englab.brq.redhat.com/covscan\
#/xmlrpc/client/"
        rpc_url = "http://cov01.lab.eng.brq.redhat.com/covscanhub/xmlrpc/kerbauth/"
        #rpc_url = "https://cov01.lab.eng.brq.redhat.com/covscan/xmlrpc/client/"
    elif options.hub_staging:
        rpc_url = "http://uqtm.lab.eng.brq.redhat.com/covscan/xmlrpc/client/"

    client = connect(rpc_url)

    #sys.excepthook = sys.__excepthook__
    before = datetime.datetime.now()
    #try:
    if options.init:
        init_scans(client)
    elif options.messaging:
        call_send_message(client)
    elif options.base and options.target:
        create_et_scan(client, options.base, options.target)
    elif options.file and options.tag_name:
        client.auth.login_krbv(login(rpc_url))
        mass_prescan(client, options.file, parser, options.tag_name)
    elif options.scan_state:
        print call_get_scan_state(client, options.scan_state)
    elif options.task_info:
        call_task_info(client, options.task_info)
    #except Exception, ex:
    #    print '---EXCEPTION---\n\n\n%s\n\n\n' % ex
    #    t = Traceback()
    #    print t.get_traceback()
    delta = datetime.datetime.now() - before
    print 'Execution took %d.%d s' % (delta.seconds, delta.microseconds)
    print "Everything is fine."
    sys.exit(0)
