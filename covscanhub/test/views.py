# -*- coding: utf-8 -*-

from covscanhub.xmlrpc.worker import email_scan_notification
from django.http import HttpResponse


def notify(request, scan_id):
    result = email_scan_notification(request, scan_id)

    return HttpResponse(result, content_type="text/plain")
