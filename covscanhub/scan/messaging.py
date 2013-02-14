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

from django.conf import settings


__all__ = (
    "send_message",
    "post_qpid_message",
)


class SenderThread(threading.Thread):
    """
    new thread that handles sending messages to broker
    """
    def __init__(self, qpid_connection, key='', message=None):
        self.key = key
        self.message = message or {}
        self.configuration = qpid_connection
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


def send_message(qpid_connection, message, key):
    """
    this function sends specified message to broker and append specified
        key to ROUTING_KEY
    """
    s = SenderThread(qpid_connection, message=message, key=key)
    s.start()


def post_qpid_message(state, etm, key):
    """Separated this into scan_notice because of dependency deadlock"""
    s = copy.deepcopy(settings.QPID_CONNECTION)
    s['KRB_PRINCIPAL'] = settings.KRB_AUTH_PRINCIPAL
    s['KRB_KEYTAB'] = settings.KRB_AUTH_KEYTAB
    send_message(s,
                 {'scan_id': etm.id,
                  'et_id': etm.et_scan_id,
                  'scan_state': state, },
                 key)
