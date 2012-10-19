# -*- coding: utf-8 -*-

from covscanhub.errata.service import create_errata_scan
from covscanhub.scan.models import SCAN_TYPES, SCAN_STATES, Scan
from kobo.django.xmlrpc.decorators import login_required


__all__ = (
    "create_errata_diff_scan",
    "get_scan_state",
)


@login_required
def create_errata_diff_scan(request, kwargs):
    """
        submit 'differential scan' task, this procedure should be used
        from errata tool

    kwargs
     - username - name of user who is requesting scan (from ET)
     - nvr - name, version, release of scanned package
     - base - previous version of package, the one to make diff against
     - id - errata ID
     - nvr_tag - tag of the package from brew
     - base_tag - tag of the base package from brew
     - rhel_version - version of enterprise linux in which will package appear
    """
    kwargs['scan_type'] = SCAN_TYPES['ERRATA']
    kwargs['task_user'] = request.user.username
    #TODO: if there will be some error, inform ET
    response = {}
    try:
        scan = create_errata_scan(kwargs)
    except RuntimeError, ex:
        response['status'] = 'ERROR'
        response['message'] = 'Scan failed to complete, error: %s' % ex
    else:
        response['id'] = scan.id
        response['status'] = 'OK'
    return response


def get_scan_state(request, scan_id):
    """
    Application returns actual state of specified scan
    Returns: state of scan. It can be one of following values (description
     can be found in  part "Requirements"):
    {'QUEUED', 'SCANNING', 'NEEDS_INSPECTION', 'WAIVED', 'PASSED'}

    type: string
    """
    response = {}
    try:
        state = SCAN_STATES.get_value(Scan.objects.get(id=scan_id).state)
    except RuntimeError, ex:
        response['status'] = 'ERROR'
        response['message'] = "Unable to retrieve scan's state, error: %s" % ex
    else:
        response['state'] = state
        response['status'] = 'OK'
    return response