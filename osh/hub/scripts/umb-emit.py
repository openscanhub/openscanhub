#!/usr/bin/python2

from __future__ import print_function

import proton
import proton.handlers
import proton.reactor


class UMBSender(proton.handlers.MessagingHandler):
    def __init__(self, key, msg):
        super(UMBSender, self).__init__()
        self.urls = ['amqps://umb-broker01.stage.api.redhat.com:5671',
                     'amqps://umb-broker02.stage.api.redhat.com:5671',
                     'amqps://umb-broker03.stage.api.redhat.com:5671',
                     'amqps://umb-broker04.stage.api.redhat.com:5671',
                     'amqps://umb-broker05.stage.api.redhat.com:5671',
                     'amqps://umb-broker06.stage.api.redhat.com:5671']
        self.cert = '/etc/osh/hub/msg-client-osh.pem'
        self.topic = 'topic://VirtualTopic.eng.covscan.scan.unfinished'
        self.scan_id = msg['scan_id']
        self.scan_state = msg['scan_state']

    def on_start(self, event):
        print('on_start')
        ssl = proton.SSLDomain(1)
        cert = str(self.cert)
        ssl.set_credentials(cert, cert, "")
        conn = event.container.connect(urls=self.urls, ssl_domain=ssl)
        print('  conn')
        event.container.create_sender(conn, self.topic)
        print('  sender')

    def on_sendable(self, event):
        print('on_sendable')
        json_msg = '{ "scan_id": %d, "scan_state": "%s" }' % (self.scan_id, self.scan_state)
        msg = proton.Message(body=json_msg)
        event.sender.send(msg)
        event.sender.close()

    def on_accepted(self, event):
        print('on_accepted')
        event.connection.close()


def main():
    key = 'covscan.scan.unfinished'
    msg = {'scan_id': 37113, 'scan_state': 'SCANNING'}
    sender = UMBSender(key, msg)
    cont = proton.reactor.Container(sender)
    cont.run()


main()
