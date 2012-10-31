# -*- coding: utf-8 -*-

from covscanhub.scan.service import post_qpid_message
from covscanhub.scan.models import SCAN_STATES
from kobo.django.xmlrpc.decorators import login_required

import random


@login_required
def send_message():
    """
    send_message()

    Posts message on qpid broker. It is using currently this configuration:
        'broker': "qpid-stage.app.eng.bos.redhat.com"
        'address': "eso.topic"
        'mechanism': "GSSAPI"
        'routing_key': 'covscan.#'

    Message has this structure:
        {
            'scan_id': int, # random ID
            'scan_state': string, # random state
        }
    """
    scan_id = random.randint(1, 10000)
    scan_state = random.choice([value for (key, value) \
in SCAN_STATES.get_mapping()])
    post_qpid_message(scan_id, scan_state)
    result = {
        'message': {
            'scan_id': scan_id,
            'scan_state': scan_state,
        },
        'comment': 'The message provided has been sent to broker, for more \
info see documentation on .../xmlrpc/kerbauth'.
    }
    return result