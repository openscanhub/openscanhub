# -*- coding: utf-8 -*-
"""
Created on Mon Aug 20 10:36:56 2012

@author: ttomecek

module for sending messages using qpid on specified broker

TODO: implement authentication via kerberos
"""

from qpid.messaging import Message, Connection  # , MessagingError
from qpid.util import URL
import threading

__all__ = (
    "send_message",
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

    def connect(self):
        """
        connect to broker and return session and connection
        """
        #fedora misses python-saslwrapper; so install it
        url = URL(self.configuration['broker'])

        connection = Connection(
            url=url,
            sasl_mechanisms=self.configuration['mechanism'],
        )

        connection.open()
        session = connection.session()

        return session, connection

    def send(self):
        try:
            session, connection = self.connect()
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