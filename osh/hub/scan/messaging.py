# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

"""
Created on Mon Aug 20 10:36:56 2012

@author: ttomecek@redhat.com, kdudka@redhat.com

module for sending messages using UMB (Unified Message Bus)
"""

import logging
import threading

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
    def __init__(self, key, msg, topic_prefix):
        super().__init__()
        self.urls = settings.UMB_BROKER_URLS
        self.cert = settings.UMB_CLIENT_CERT
        self.topic = topic_prefix + '.' + key
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
    def __init__(self, key, msg, topic_prefix):
        threading.Thread.__init__(self)
        self.key = key
        self.msg = msg
        self.topic_prefix = topic_prefix

    def run(self):
        sender = UMBSender(self.key, self.msg, self.topic_prefix)
        cont = proton.reactor.Container(sender)
        cont.run()


def send_message(message, key):
    """
    this function sends specified message to broker and append specified
        key to ROUTING_KEY
    """
    tp_list = settings.UMB_TOPIC_PREFIX
    if isinstance(tp_list, str):
        # wrap string as a one-item list
        tp_list = [tp_list]

    # start a separate instance of SenderThread for each topic prefix in the list
    for topic_prefix in tp_list:
        s = SenderThread(key, message, topic_prefix)
        s.start()


def post_qpid_message(state, etm, key):
    """Separated this into scan_notice because of dependency deadlock"""
    logger.info('message bus: %s %s', etm, state)
    message = {'scan_id': etm.id, 'scan_state': state}
    send_message(message, key)
