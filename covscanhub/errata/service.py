# -*- coding: utf-8 -*-


from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
import os
#import messaging.send_message
from django.conf import settings
import brew
from covscanhub.scan.service import run_diff
from covscanhub.scan.models import Scan, SCAN_STATES, Tag
from covscanhub.waiving.service import create_results
from kobo.hub.models import Task
import copy
            
def create_errata_base_scan(kwargs, task_id):
    options = {}

    task_user = kwargs['task_user']
    username = kwargs['username']
    scan_type = SCAN_STATES['ERRATA_BASE']
    base_obj = None
    nvr = kwargs['base']
    task_label = nvr
    
    #TODO change this
    tag = kwargs['tag']
    tag_obj = Tag.objects.get(name=tag)
    options['mock_config'] = tag_obj.mock.name
    
    priority = kwargs.get('priority', settings.ET_SCAN_PRIORITY) + 1
    comment = 'Errata Tool Base scan of %s requested by %s' % \
        (nvr, kwargs['base'])

    # Test if SRPM exists
    brew_proxy = brew.ClientSession(settings.BREW_HUB)
    try:
        brew_proxy.getBuild(nvr)
        options['brew_build'] = nvr
    except brew.GenericError:
        raise RuntimeError("Brew build of package %s does not exist" % nvr)

    task_id = Task.create_task(
        owner_name=task_user,
        label=task_label,
        method='ErrataDiffBuild',
        args={}, # I want to add scan's id here, so I update it later
        comment=comment,
        state=SCAN_STATES["QUEUED"],
        priority=priority,
        parent_id=task_id,
    )
    task_dir = Task.get_task_dir(task_id)

    if not os.path.isdir(task_dir):
        try:
            os.makedirs(task_dir, mode=0755)
        except OSError, ex:
            if ex.errno != 17:
                raise

    # if base is specified, try to fetch it; if it doesn't exist, create
    # new task for it
    scan = Scan.create_scan(scan_type=scan_type, nvr=nvr, task_id=task_id,
                            tag=tag_obj, base=base_obj, username=username)
    scan.save()

    options['scan_id'] = scan.id
    task = Task.objects.get(id=task_id)
    task.args = options
    task.save()
    
    return scan

def create_errata_scan(kwargs):
    """
        create scan of a package and perform diff on results against specified
        version
        options of this scan are in dict 'kwargs'

        kwargs
         - scan_type - type of scan (SCAN_TYPES in covscanhub.scan.models)
         - username - name of user who is requesting scan (from ET)
         - task_user - username from request.user.username
         - nvr - name, version, release of scanned package
         - base - previous version of package, the one to make diff against
         - id - errata ID
         - tag - tag from brew
    """
    options = {}

    #from request.user
    task_user = kwargs['task_user']

    #supplied by scan initiator
    username = kwargs['username']
    scan_type = kwargs['scan_type']
    nvr = kwargs['nvr']
    base = kwargs['base']
    options['errata_id'] = kwargs['id']

    #Label, description or any reason for this task.
    task_label = nvr

    tag = kwargs['tag']
    priority = kwargs.get('priority', settings.ET_SCAN_PRIORITY)

    #if kwargs does not have 'id', it is base scan
    comment = 'Errata Tool Scan of %s' % nvr

    #does tag exist?
    try:
        tag_obj = Tag.objects.get(name=tag)
    except ObjectDoesNotExist:
        raise ObjectDoesNotExist("Unknown tag: %s" % tag)
    if not tag_obj.mock.enabled:
        raise RuntimeError("Mock config is disabled: %s" % tag_obj.mock)
    options['mock_config'] = tag_obj.mock.name

    if nvr.endswith(".src.rpm"):
        srpm = nvr[:-8]
    else:
        srpm = nvr

    # Test if SRPM exists
    brew_proxy = brew.ClientSession(settings.BREW_HUB)
    try:
        brew_proxy.getBuild(srpm)
        options['brew_build'] = srpm
    except brew.GenericError:
        raise RuntimeError("Brew build of package %s does not exist" % nvr)

    task_id = Task.create_task(
        owner_name=task_user,
        label=task_label,
        method='ErrataDiffBuild',
        args={},  # I want to add scan's id here, so I update it later
        comment=comment,
        state=SCAN_STATES["QUEUED"],
        priority=priority,
    )
    task_dir = Task.get_task_dir(task_id)

    if not os.path.isdir(task_dir):
        try:
            os.makedirs(task_dir, mode=0755)
        except OSError, ex:
            if ex.errno != 17:
                raise

    # if base is specified, try to fetch it; if it doesn't exist, create
    # new task for it
    base_obj = None
    if base:
        try:
            base_obj = Scan.objects.get(nvr=base)
        except ObjectDoesNotExist:
            parent_task = Task.objects.get(id=task_id)            
            base_obj = create_errata_base_scan(copy.deepcopy(kwargs), task_id)

            # wait has to be after creation of new subtask
            # TODO wait should be executed in one transaction with creation of
            # child
            parent_task.wait()
        except MultipleObjectsReturned:
            #return latest, but this shouldnt happened
            base_obj = Task.objects.filter(base=base).order_by('-dt_created')[0]

    scan = Scan.create_scan(scan_type=scan_type, nvr=nvr, task_id=task_id,
                            tag=tag_obj, base=base_obj, username=username)

    options['scan_id'] = scan.id
    task = Task.objects.get(id=task_id)
    task.args = options
    task.save()
    
    return scan


def finish_scanning(scan_id):
    scan = Scan.objects.get(id=scan_id)

    size = None    
    if scan.base:
        size = run_diff(scan_id)
        # TODO insert found defects into database

    if scan.is_errata_scan():
        create_results(scan)
        if size is None or size == 0:
            scan.state = SCAN_STATES['PASSED']
        else:
            scan.state = SCAN_STATES['NEEDS_INSPECTION']
    elif scan.is_user_scan():
        scan.state = SCAN_STATES['FINISHED']
    scan.save()