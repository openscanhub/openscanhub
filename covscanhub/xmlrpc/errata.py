# -*- coding: utf-8 -*-

import brew

from covscanhub.errata.service import create_errata_scan
from covscanhub.other.exceptions import BrewException
from covscanhub.scan.models import SCAN_TYPES, SCAN_STATES, Scan

from kobo.django.xmlrpc.decorators import login_required

from django.contrib.auth.decorators import user_passes_test


__all__ = (
    "create_errata_diff_scan",
    "get_scan_state",
)


@login_required
@user_passes_test(lambda u: u.has_perm('scan.errata_xmlrpc_scan'))
def create_errata_diff_scan(request, kwargs):
    """
    create_errata_diff_scan(kwargs)

        submits 'differential scan' task, this procedure should be used
        from errata tool

    @param kwargs:
     - username - name of user who is requesting scan (from ET)
     - nvr - name, version, release of scanned package
     - base - previous version of package, the one to make diff against
     - id - errata ID
     - nvr_tag - tag of the package from brew
     - base_tag - tag of the base package from brew
     - rhel_version - version of enterprise linux in which will package appear
    @type kwargs: dictionary
    @rtype: dictionary
    @return:
     - status: status message: { 'OK', 'ERROR' }
     - message: in case of error, here is detailed message
     - id: ID of submitted scan
    """
    kwargs['scan_type'] = SCAN_TYPES['ERRATA']
    kwargs['task_user'] = request.user.username

    response = {}
    try:
        scan = create_errata_scan(kwargs)
    except brew.GenericError, ex:
        response['status'] = 'ERROR'
        response['message'] = 'Requested build does not exist in brew: %s' % ex
    except BrewException, ex:
        response['status'] = 'ERROR'
        response['message'] = '%s' % ex        
    except RuntimeError, ex:
        response['status'] = 'ERROR'
        response['message'] = 'Scan failed to complete, error: %s' % ex
    else:
        response['id'] = scan.id
        response['status'] = 'OK'
    return response


def get_scan_state(request, scan_id):
    """
    get_scan_state(scan_id)

        Function that informs requestor about actual state of specified scan

    @param scan_id: ID of requested scan
    @type scan_id: string or int

    @rtype: dictionary
    @return:
     - status: status message: { 'OK', 'ERROR' }
     - message: in case of error, here is detailed message
     - state: state of scan. It can be one of following values (description
         can be found in etherpad in part "Requirements"):
       {'QUEUED', 'SCANNING', 'NEEDS_INSPECTION', 'WAIVED', 'PASSED'}
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