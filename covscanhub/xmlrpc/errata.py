# -*- coding: utf-8 -*-

import brew
import logging

from covscanhub.errata.service import create_errata_scan
from covscanhub.other.exceptions import BrewException
from covscanhub.scan.models import SCAN_TYPES, SCAN_STATES, Scan

from kobo.django.xmlrpc.decorators import login_required

from django.core.exceptions import ObjectDoesNotExist


__all__ = (
    "create_errata_diff_scan",
    "get_scan_state",
)

logger = logging.getLogger(__name__)


@login_required
def create_errata_diff_scan(request, kwargs):
    """
    create_errata_diff_scan(kwargs)

        submits 'differential scan' task, this procedure should be used
        from errata tool

    @param kwargs:
     - package_owner - name of the package for the advisory owner
     - target - name, version, release of scanned package (brew build)
     - base - previous version of package, the one to make diff against
     - id - ET internal id for the scan record in ET
     - errata_id - the ET internal id of the advisory that the build is part of
     - rhel_version - short tag of rhel version -- product (e. g. 'RHEL-6.3.Z')
     - release - The advisory's release ('ASYNC', 'RHEL-.*', 'MRG.*')
    @type kwargs: dictionary
    @rtype: dictionary
    @return:
     - status: status message: { 'OK', 'ERROR' }
     - message: in case of error, here is detailed message
     - id: ID of submitted scan (it is the ID used for waiver's URL)

     for more info see http://etherpad.corp.redhat.com/Covscan-ErrataTool-Integration
    """
    logger.info('Incoming scan request: %s.', kwargs)
    if not request.user.has_perm('scan.errata_xmlrpc_scan'):
        response = {}
        response['status'] = 'ERROR'
        response['message'] = 'You are not authorized to execute this \
function.'
        logger.info('User %s tried to submit scan.', request.user.username)
        return response

    if kwargs == {}:
        response = {}
        response['status'] = 'ERROR'
        response['message'] = 'Provided dictionary (map/Hash) is empty.'
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
       {'QUEUED', 'SCANNING', 'NEEDS_INSPECTION', 'WAIVED', 'PASSED',
        'FAILED', 'BASE_SCANNING', 'CANCELED'}
    """
    logger.info('%s', scan_id)
    response = {}
    try:
        scan = Scan.objects.get(id=scan_id)
    except ObjectDoesNotExist:
        response['status'] = 'ERROR'
        response['message'] = "Scan %s does not exist." % scan_id
    except RuntimeError, ex:
        response['status'] = 'ERROR'
        response['message'] = "Unable to retrieve scan's state, error: %s" % ex
    else:
        state = SCAN_STATES.get_value(scan.state)
        response['state'] = state
        response['status'] = 'OK'
    return response
