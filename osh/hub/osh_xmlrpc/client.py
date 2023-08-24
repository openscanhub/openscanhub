# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import kobo.hub.xmlrpc.client as kobo_xmlrpc_client
from kobo.django.xmlrpc.decorators import login_required

from osh.hub.scan.models import ScanBinding
from osh.hub.scan.xmlrpc_helper import cancel_scan


@login_required
def cancel_task(request, task_id):
    response = kobo_xmlrpc_client.cancel_task(request, task_id)

    # cancel the corresponding scan
    sb = ScanBinding.objects.filter(task=task_id).first()
    if sb is not None:
        cancel_scan(sb)

    return response
