# -*- coding: utf-8 -*-

import re
import logging

from django.core.exceptions import ObjectDoesNotExist

from kobo.hub.models import Task
from kobo.django.xmlrpc.decorators import login_required, admin_required

from covscanhub.errata.scanner import create_diff_task2, ClientScanScheduler, ClientDiffPatchesScanScheduler
from covscanhub.scan.models import Package, Tag, ClientAnalyzer, Profile


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
