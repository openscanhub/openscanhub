# -*- coding: utf-8 -*-
"""
Created on Mon Aug 20 10:36:56 2012

@author: ttomecek@redhat.com

module for sending messages using qpid on specified broker
"""

from qpid.messaging import Message, Connection  # , MessagingError
from qpid.messaging.exceptions import AuthenticationFailure
from qpid.util import URL
import threading
import os
import krbV
import copy
import logging
import proton
import proton.handlers
import proton.reactor

from django.conf import settings


__all__ = (
    "send_message",
    "post_qpid_message",
)

logger = logging.getLogger(__name__)


class UMBSender(proton.handlers.MessagingHandler):
    def __init__(self, key, msg):
        super(UMBSender, self).__init__()
        self.urls = settings.UMB_BROKER_URLS
        self.cert = settings.UMB_CLIENT_CERT
        self.topic = settings.UMB_TOPIC_PREFIX + '.' + key
        self.scan_id = msg['scan_id']
        self.scan_state = msg['scan_state']

    def on_start(self, event):
        ssl = proton.SSLDomain(1)
        cert = str(self.cert)
        ssl.set_credentials(cert, cert, "")
        conn = event.container.connect(urls=self.urls, ssl_domain=ssl)
        event.container.create_sender(conn, self.topic)

    def on_sendable(self, event):
        json_msg = '{ "scan_id": %d, "scan_state": "%s" }' % (self.scan_id, self.scan_state)
        msg = proton.Message(body=json_msg)
        event.sender.send(msg)
        event.sender.close()

    def on_accepted(self, event):
        event.connection.close()


class SenderThread(threading.Thread):
    """
    new thread that handles sending messages to broker
    """
    def __init__(self, key, msg):
        threading.Thread.__init__(self)
        self.key = key
        self.msg = msg

    def run(self):
        sender = UMBSender(self.key, self.msg)
        cont = proton.reactor.Container(sender)
        cont.run()


class SenderThreadLegacy(threading.Thread):
    """
    new thread that handles sending messages to broker
    """
    def __init__(self, qpid_conf, key='', message=None):
        self.key = key
        self.message = message or {}
        self.configuration = qpid_conf
        threading.Thread.__init__(self)

    def krb_init(self):
        """
            self.configuration['KRB_PRINCIPAL'] -- name of principal
            self.configuration['KRB_KEYTAB'] -- path to keytab
        """
        principal = self.configuration['KRB_PRINCIPAL']
        keytab = self.configuration['KRB_KEYTAB']
        if principal is None:
            raise RuntimeError('Principal not specified.')
        if not keytab or not os.path.exists(keytab):
            raise RuntimeError('Keytab (%s) does not exist.' % keytab)
        ccname = 'MEMORY:'
        os.environ['KRB5CCNAME'] = ccname
        ctx = krbV.default_context()
        ccache = krbV.CCache(name=ccname, context=ctx)
        cprinc = krbV.Principal(name=principal, context=ctx)
        ccache.init(principal=cprinc)
        keytab_obj = krbV.Keytab(name='FILE:' + keytab, context=ctx)
        ccache.init_creds_keytab(principal=cprinc, keytab=keytab_obj)

    def connect(self):
        """
        connect to broker and return session and connection, if needed
         initialize kerberos CCache from keytab
        """
        #fedora misses python-saslwrapper; so install it
        url = URL(self.configuration['broker'])

        retry = 2
        is_live = False
        while retry and not is_live:
            try:
                retry -= 1
                #create connection and try to open it
                connection = Connection(
                    url=url,
                    sasl_mechanisms=self.configuration['mechanism'],
                    transport='ssl',
                    port=5671,
                )
                connection.open()
                is_live = True
            except AuthenticationFailure:
                if connection.opened():
                    connection.close()
                if not retry:
                    #kerb init didn't help, raise again
                    raise
                else:
                    #initialize kerberos -- using principal and keytab
                    self.krb_init()

        session = connection.session()

        return session, connection

    def send(self):
        session, connection = self.connect()
        try:
            sender = session.sender(self.configuration['address'])

            final_key = self.configuration['routing_key'] + '.' + self.key
            sender.send(Message(subject=final_key,
                                content=self.message))
            session.acknowledge()
        finally:
            connection.close()

    def run(self):
        self.send()


def send_message(qpid_conf, message, key):
    """
    this function sends specified message to broker and append specified
        key to ROUTING_KEY
    """
    s = SenderThread(key, message)
    s.start()

    s = SenderThreadLegacy(qpid_conf, message=message, key=key)
    s.start()


def post_qpid_message(state, etm, key):
    """Separated this into scan_notice because of dependency deadlock"""
    logger.info('message bus: %s %s', etm, state)
    qpid_conf = copy.deepcopy(settings.QPID_CONNECTION)
    qpid_conf['KRB_PRINCIPAL'] = settings.KRB_AUTH_PRINCIPAL_SERVICE
    qpid_conf['KRB_KEYTAB'] = settings.KRB_AUTH_KEYTAB_SERVICE
    send_message(qpid_conf,
                 {'scan_id': etm.id,
                  #'et_id': etm.et_scan_id,
                  'scan_state': state, },
                 key)
