# -*- coding: utf-8 -*-

from covscanhub.scan.notify import send_scan_notification
from django.http import HttpResponse


def notify(request, scan_id):
    result = send_scan_notification(request, scan_id)

    return HttpResponse(result, content_type="text/plain")
