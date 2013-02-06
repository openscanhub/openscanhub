# -*- coding: utf-8 -*-

import brew
import logging

from covscanhub.errata.service import create_errata_scan
from covscanhub.other.exceptions import BrewException
from covscanhub.scan.models import SCAN_TYPES, SCAN_STATES, Scan

from kobo.django.xmlrpc.decorators import login_required


__all__ = (
    "create_errata_diff_scan",
    "get_scan_state",
)


@login_required
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
    if not request.user.has_perm('scan.errata_xmlrpc_scan'):
        response = {}
        response['status'] = 'ERROR'
        response['message'] = 'You are not authorized to execute this \
function.'
        logging.info('User %s tried to submit scan.', request.user.username)
        return response

    if kwargs == {}:
        response = {}
        response['status'] = 'ERROR'
        response['message'] = 'Provided dictionary (map) is empty.'
        return response

    kwargs['scan_type'] = SCAN_TYPES['ERRATA']
    kwargs['task_user'] = request.user.username

    response = {}
    try:
        sb = create_errata_scan(kwargs)
    except brew.GenericError, ex:
        response['status'] = 'ERROR'
        response['message'] = 'Requested build does not exist in brew: %s' % ex
    except BrewException, ex:
        response['status'] = 'ERROR'
        response['message'] = '%s' % ex
    except RuntimeError, ex:
        response['status'] = 'ERROR'
        response['message'] = 'Unable to submit the scan, error: %s' % ex
    except Exception, ex:
        response['status'] = 'ERROR'
        response['message'] = '%s' % ex
    else:
        response['id'] = sb.id
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