# -*- coding: utf-8 -*-

import logging

from kobo.django.auth.models import User

from covscanhub.errata.scanner import handle_scan

from covscanhub.scan.models import SCAN_STATES, ETMapping, \
    AppSettings, REQUEST_STATES, Scan

from kobo.django.xmlrpc.decorators import login_required

from django.core.exceptions import ObjectDoesNotExist


__all__ = (
    "create_errata_diff_scan",
    "get_scan_state",
    "get_filtered_scan_list",
)

logger = logging.getLogger("covscanhub")


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
     - status: status message: { 'OK', 'ERROR', 'INELIGIBLE' }
     - message: in case of error, here is detailed message
     - id: ID of mapping between ET_IDs and covscan IDs. This may be used to
       access waiver upon scan creation (you may use both URLs, same content
       is served):
           <hub_prefix>/waiving/et_mapping/<id>
           <hub_prefix>/waiving/et/<et_inernal_covscan_id>

     for more info see http://etherpad.corp.redhat.com/Covscan-ErrataTool-Integration
    """
    logger.info('[CREATE_SCAN] %s', kwargs)
    # either there is no need to check user or user has to have permission to
    # submit scans
    if AppSettings.setting_check_user_can_submit() and \
            not request.user.has_perm('scan.errata_xmlrpc_scan'):
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

    kwargs['task_user'] = request.user.username

    response = handle_scan(kwargs)

    logger.info('[CREATE_SCAN] => %s', response)
    return response


def get_filtered_scan_list(request, kwargs):
    """
    get_filtered_scan_list(kwargs)

        Returns scans which fits kwargs filters, multiple filters can be used at the same time.
        Method should be used through API. Available filters are:

    @param kwargs:
     - id - id of the scan
     - target - target of the scan
     - base - base of the scan
     - state - state in string form according to enum SCAN_STATES
     - username - owner of the scan
     - release - system release of the scan
    @type kwargs: dictionary
    @return:
     - status: status message: { 'OK', 'ERROR' }
     - message: in case of error, here is detailed message
     - count: number of returned scans
     - scans: info about selected scans in a list of dictionaries

     Basic usage:

        for scan in returned_object['scans']:  # goes through all scans
            print scan['nvr']                  # use which dictionary value you need

     @see get_filtered_scan_list in covscan.covscan_api for more details

    """

    kwargs = __setup_kwargs(kwargs)
    logger.info('[FILTER_SCANS] %s', kwargs)
    ret_value = __convert_names_to_numbers(kwargs)
    if ret_value:
        return ret_value

    query_set = Scan.objects.filter(**kwargs).select_related() \
        .values('username__username',
                'username__email',
                'package__name',
                'package__blocked',
                'package__eligible',
                'date_submitted',
                'enabled',
                'id',
                'nvr',
                'base_id',
                'base__nvr',
                'last_access',
                'scan_type',
                'state',
                'tag__release__tag',
                'tag__name',
                )
    return {'status': 'OK', 'count': query_set.count(), 'scans': __rename_keys(list(query_set)) }


def __setup_kwargs(kwargs):
    """
    Renames keys and removes None values from dictionary
    @param kwargs: dictionary to be modified
    @return:
    """

    kwargs['nvr'] = kwargs.pop('target', None)
    kwargs['base__nvr'] = kwargs.pop('base', None)
    kwargs['tag__release__tag'] = kwargs.pop('release', None)
    kwargs = dict(filter(lambda (k, v): v is not None, kwargs.items()))
    return kwargs


def __convert_names_to_numbers(kwargs):
    """
    Private method, converts username to user_id & scan state name to state_id.
    Kwargs arguments are modified from names to numbers.
    @param kwargs: dictionary to be changed
    @return: dictionary with status message if username or scan state does not exist
    """

    if 'username' in kwargs:
        try:
            kwargs['username'] = User.objects.get(username=kwargs['username']).id
        except ObjectDoesNotExist as e:
            return {'status': 'ERROR', 'message': e.message}

    if 'state' in kwargs:
        state_number = SCAN_STATES.get_num(kwargs['state'])
        if not state_number:
            return {'status': 'ERROR', 'message': 'Scan state ' + kwargs['state'] + ' does not exist.'}
        kwargs['state'] = state_number


def __rename_keys(scans_list):
    # The best way would be to use SQL query with renamed values, but django doesn't support it very cleverly
    translation_table = {'username__username'   : 'user_name',
                         'username__email'      : 'user_email',
                         'package__name'        : 'package_name',
                         'package__blocked'     : 'package_is_blocked',
                         'package__eligible'    : 'package_is_eligible',
                         'last_access'          : 'date_last_accessed',
                         'nvr'                  : 'target',
                         'enabled'              : 'is_enabled',
                         'base__nvr'            : 'base_target',
                         'tag__release__tag'    : 'release',
                         'tag__name'            : 'tag_name',
                         }
    for scan in scans_list:
        for old_name, new_name in translation_table.items():
            scan[new_name] = scan.pop(old_name)
    return scans_list


def get_scan_state(request, etm_id):
    """
    get_scan_state(scan_id)

        Function that informs requestor about actual state of specified scan

    @param scan_id: ID of requested scan (returned by create_scan function)
    @type scan_id: string or int

    @rtype: dictionary
    @return:
     - status: status message: { 'OK', 'ERROR', 'INELIGIBLE' }
     - message: in case of error, here is detailed message
     - state: state of scan. It can be one of following values (description
         can be found in etherpad in part "Requirements"):
       {'QUEUED', 'SCANNING', 'NEEDS_INSPECTION', 'WAIVED', 'PASSED',
        'FAILED', 'BASE_SCANNING', 'CANCELED', 'DISPUTED'}

    More info can be found here:
        http://etherpad.corp.redhat.com/Covscan-ErrataTool-Integration
    """

    logger.info('[SCAN_STATE] %s', etm_id)
    response = {}
    try:
        etm = ETMapping.objects.get(id=etm_id)
    except ObjectDoesNotExist:
        response['status'] = 'ERROR'
        response['message'] = "Scan %s does not exist." % etm_id
    except Exception, ex:
        response['status'] = 'ERROR'
        response['message'] = "Unable to retrieve scan's state, error: %s" % ex
    else:
        message = getattr(etm, 'comment', '')
        if message:
            response['message'] = message
        status_number = getattr(etm, 'state', REQUEST_STATES.get_num("OK"))
        response['status'] = REQUEST_STATES.get_value(status_number)
        if etm.latest_run:
            response['state'] = SCAN_STATES.get_value(
                etm.latest_run.scan.state)
    logger.info('[SCAN_STATE] => %s', response)
    return response
