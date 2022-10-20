#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 20 10:36:56 2012

@author: Tomas Tomecek <ttomecek@redhat.com>
"""

import datetime
import sys

import kobo.process
from qpid.messaging import Connection, exceptions
from qpid.util import URL


def daemon_main():
    key = 'covscan.scan.#'
    BROKER = "qpid-stage.app.eng.bos.redhat.com"
    mechanism = "GSSAPI"
    url = URL(BROKER)
    with open("/var/tmp/qpid_listener.log", "a+") as output:
        output.write("Daemon started.\n")
        connection = Connection(url=url, sasl_mechanisms=mechanism)
        try:
            connection.open()
            session = connection.session()

            receiver_address = """tmp.covscan_rec_queue; { create: receiver,
                                                   node: { type: queue, durable: False,
                                                           x-declare: { exclusive: False,
                                                                        auto-delete: True,
                                                                        arguments: {'qpid.policy_type': ring,
                                                                                    'qpid.max_size': 50000000}},
                                                           x-bindings: [{exchange:'eso.topic', queue:'tmp.covscan_rec_queue', key:'%s'}] }}""" % key

            receiver = session.receiver(receiver_address)

            while True:
                # message = receiver.fetch(timeout=1)
                message = receiver.fetch()
                if message:
                    output.write('%s Accepted message %s [%s]\n' % (
                        datetime.datetime.now(), message.subject, message.content))
                session.acknowledge()

        except (exceptions.ConnectionError, exceptions.SessionError,
                exceptions.TransactionError, exceptions.MessagingError) as e:
            output.write(f"\n{repr(e)}\n")
        finally:
            connection.close()
        output.write("Exiting.\n")
    sys.exit(0)


def main():
    kobo.process.daemonize(daemon_main,
                           daemon_pid_file='/var/tmp/qpid_listener.pid',
                           daemon_out_log="/var/tmp/qpid_listener_error.log",
                           daemon_err_log="/var/tmp/qpid_listener_error.log",
                           )


if __name__ == "__main__":
    sys.exit(main())
