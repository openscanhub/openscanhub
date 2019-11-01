# -*- coding: utf-8 -*-

import re
import logging

from django.core.exceptions import ObjectDoesNotExist

from kobo.hub.models import Task
from kobo.django.xmlrpc.decorators import login_required

from covscanhub.errata.scanner import create_diff_task2, ClientScanScheduler, ClientDiffPatchesScanScheduler
from covscanhub.other.constants import DEFAULT_SCAN_LIMIT
from covscanhub.scan.models import ClientAnalyzer, Profile, Scan, SCAN_STATES
from kobo.django.auth.models import User

logger = logging.getLogger("covscanhub")

__all__ = (
    "diff_build",
    "mock_build",
    "create_user_diff_task",
    "get_task_info",
    "find_tasks",
    "list_analyzers",
    "list_profiles",
    "check_analyzers",
    "get_filtered_scan_list",
)


@login_required
def diff_build(request, mock_config, comment, options, *args, **kwargs):
    """
    diff_build(mock_config, comment, options, *args, **kwargs)

    options = {
        'upload_id': when uploading srpm directly via FileUpload
        'brew_build': nvr of build in brew
    }
    """
    options['comment'] = comment
    options['mock_config'] = mock_config
    options['task_user'] = request.user.username
    options['user'] = request.user
    cs = ClientDiffPatchesScanScheduler(options)
    cs.prepare_args()
    return cs.spawn()


@login_required
def mock_build(request, mock_config, comment, options, *args, **kwargs):
    """
    mock_build(mock_config, comment, options, *args, **kwargs)

    options = {
        'upload_id': when uploading srpm directly via FileUpload
        'brew_build': nvr of build in brew
    }
    """
    options['comment'] = comment
    options['mock_config'] = mock_config
    options['task_user'] = request.user.username
    options['user'] = request.user
    cs = ClientScanScheduler(options)
    cs.prepare_args()
    return cs.spawn()


@login_required
def create_user_diff_task(request, hub_opts, task_opts):
    """
        create scan of a package and perform diff on results against specified
        version

        kwargs:
         - nvr_srpm - name, version, release of scanned package
         - nvr_upload_id - upload id for target, so worker is able to download it
         - nvr_brew_build - NVR of package to be downloaded from brew
         - base_srpm - name, version, release of base package
         - base_upload_id - upload id for base, so worker is able to download it
         - base_brew_build - NVR of base package to be downloaded from brew
         - nvr_mock - mock config
         - base_mock - mock config
    """
    hub_opts['task_user'] = request.user.username
    hub_opts['user'] = request.user
    logger.debug("Client diff task: %s, %s", hub_opts, task_opts)
    return create_diff_task2(hub_opts, task_opts)


def get_filtered_scan_list(request, kwargs, filter_scan_limit=DEFAULT_SCAN_LIMIT):
    """
    get_filtered_scan_list(kwargs, filter_scan_limit)

        Returns scans which fits kwargs filters, multiple filters can be used at the same time.
        Method should be used through API. Available filters are:

    @param kwargs:
     - id - id of the scan
     - target - target of the scan
     - base - base of the scan
     - state - state in string form according to enum SCAN_STATES
     - owner - owner of the scan
     - release - system release of the scan
    @type kwargs: dictionary
    @param filter_scan_limit:
     - maximum number of scans which can be returned
     - if the query exceeds the limit, error message is returned
     - parameter is optional, if not set DEFAULT_SCAN_LIMIT is used
    @return:
     - status: status message: { 'OK', 'ERROR' }
     - message: in case of error, here is detailed message
     - count: number of returned scans
     - scans: info about selected scans in a list of dictionaries, sorted by submission date

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
        .order_by('-date_submitted') \
        .values('username__username',
                'username__email',
                'package__name',
                'package__blocked',
                'package__eligible',
                'date_submitted',
                'enabled',
                'scanbinding__id',
                'nvr',
                'base_id',
                'base__nvr',
                'last_access',
                'scan_type',
                'state',
                'tag__release__tag',
                'tag__name',
                )
    results_count = query_set.count()
    if results_count > filter_scan_limit:
        return {'status': 'ERROR', 'message': 'Limit exceeded, returning first ' + str(filter_scan_limit) + ' scans.',
                'count': filter_scan_limit, 'scans': __rename_keys(list(query_set[:filter_scan_limit]))}

    return {'status': 'OK', 'count': results_count, 'scans': __rename_keys(list(query_set))}


def __setup_kwargs(kwargs):
    """
    Renames keys and removes None values from dictionary
    @param kwargs: dictionary to be modified
    @return: kwargs
    """

    kwargs['nvr'] = kwargs.pop('target', None)
    kwargs['scanbinding__id'] = kwargs.pop('id', None) # conversion to correct id
    kwargs['base__nvr'] = kwargs.pop('base', None)
    kwargs['tag__release__tag'] = kwargs.pop('release', None)
    kwargs = {k:v for k, v in kwargs.items() if v is not None}
    return kwargs


def __convert_names_to_numbers(kwargs):
    """
    Private method, converts owner to user_id & scan state name to state_id.
    Kwargs arguments are modified from names to numbers.
    @param kwargs: dictionary to be changed
    @return: dictionary with status message if owner or scan state does not exist
    """

    if 'owner' in kwargs:
        try:
            kwargs['username'] = User.objects.get(username=kwargs.pop('owner')).id
        except ObjectDoesNotExist as e:
            return {'status': 'ERROR', 'message': e.message}

    if 'state' in kwargs:
        state_number = SCAN_STATES.get_num(kwargs['state'])
        if not state_number:
            return {'status': 'ERROR', 'message': 'Scan state ' + kwargs['state'] + ' does not exist.'}
        kwargs['state'] = state_number


def __rename_keys(scans_list):
    # The best way would be to use SQL query with renamed values, but django doesn't support it very cleverly
    translation_table = {'username__username'   : 'owner_name',
                         'username__email'      : 'owner_email',
                         'package__name'        : 'package_name',
                         'package__blocked'     : 'package_is_blocked',
                         'package__eligible'    : 'package_is_eligible',
                         'last_access'          : 'date_last_accessed',
                         'nvr'                  : 'target',
                         'enabled'              : 'is_enabled',
                         'base__nvr'            : 'base_target',
                         'tag__release__tag'    : 'release',
                         'tag__name'            : 'tag_name',
                         'scanbinding__id'      : 'id',
                         }
    for scan in scans_list:
        for old_name, new_name in translation_table.items():
            scan[new_name] = scan.pop(old_name)
    return scans_list


def get_task_info(request, task_id):
    """
    get_task_info(task_id) -> {...}

    provide info about specified task, if task does not exist,
    return empty dict (map/hash)
    """
    result = {}
    try:
        task = Task.objects.get(pk=task_id)
        result = task.export()
    except ObjectDoesNotExist:
        pass
    return result


def find_tasks(request, query):
    """
    find_tasks(request, query) -> [ <id>, <id>, ... ]

    Query hub to get IDs of tasks specified by query.
    Query is a dict (hash/map), it has to have exactly one of these keys:
     * 'package_name': return all task IDs for provided package
     * 'nvr': search by specific NVR
     * 'regex': find by provided regex (this is not match, but find, if you
                want match, change your regex to "^<regex>$")

    Returned list is ordered by date, when task finished -- latest task is
    first. Unfinished tasks are at the tail. If there is any problem with
    querying, empty list is returned.
    """
    if not isinstance(query, dict):
        return []
    nvr = query.get('nvr', None)
    package_name = query.get('package_name', None)
    regex = query.get('regex', None)

    result = []
    tasks = None
    if nvr:
        tasks = Task.objects.filter(label=nvr)
    if package_name:
        tasks = Task.objects.filter(label__regex=package_name + "-\d")
    elif regex:
        tasks = Task.objects.filter(label__regex=regex)
    if tasks is not None:
        result = list(tasks.order_by("-dt_finished").values_list(
            "id", flat=True))
    return result


def list_analyzers(request):
    return ClientAnalyzer.objects.export_available()


def list_profiles(request):
    return list(Profile.objects.export_available())


def check_analyzers(request, analyzers):
    a_list = re.split('[,:;]', analyzers.strip())

    for analyzer in a_list:
        if not ClientAnalyzer.objects.is_valid(analyzer):
            return "Analyzer %s is not available." % analyzer
