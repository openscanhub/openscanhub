# -*- coding: utf-8 -*-

from covscanhub.errata.service import create_errata_scan
from covscanhub.scan.models import SCAN_TYPES
from kobo.django.xmlrpc.decorators import login_required


@login_required
def create_errata_diff_scan(request, kwargs):
    """
        submit 'differential scan' task, this procedure should be used
        from errata tool

        kwargs:
         - username - name of user who is requesting scan (from ET)
         - nvr - name, version, release of scanned package
         - base - previous version of package, the one to make diff against
         - id - errata ID
         - tag - tag from brew
    """
    kwargs['scan_type'] = SCAN_TYPES['ERRATA']
    kwargs['task_user'] = request.user.username
    create_errata_scan(kwargs)