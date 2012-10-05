# -*- coding: utf-8 -*-


from covscanhub.scan.models import Scan, Task, SCAN_STATES, Tag, SCAN_TYPES, MockConfig
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from kobo.shortcuts import run
import os
import pipes
#import messaging.send_message
#import django.conf.settings
import brew
import shutil
from covscanhub.scan.service import get_scan_by_nvr, run_diff


ET_SCAN_PRIORITY = 20

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
    priority = ET_SCAN_PRIORITY
    if kwargs['id'] is None:
        comment = 'Errata Tool Base scan generated for %s' % kwargs['requestor']
    else:
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
    # XXX: hardcoded
    brew_proxy = brew.ClientSession("http://brewhub.devel.redhat.com/brewhub")
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
        parent_id=kwargs.get('parent_task', None),
    )
    task_dir = Task.get_task_dir(task_id)

    if not os.path.isdir(task_dir):
        try:
            os.makedirs(task_dir, mode=0755)
        except OSError, ex:
            if ex.errno != 17:
                raise

    if base:
        try:
            base_obj = get_scan_by_nvr(base)
        except ObjectDoesNotExist:
            import copy
            o = copy.deepcopy(kwargs)
            o['nvr'] = base
            o['base'] = None
            o['requestor'] = nvr
            o['priority'] = o['priority'] + 1
            o['id'] = None
            o['parent_task'] = task_id
            #TODO base tag vs. parent tag
            
            create_errata_scan(o)

            #wait has to be after creation of new subtask            
            t = Task.objects.get(id=task_id)
            t.wait()            
        except MultipleObjectsReturned:
            """
            TODO what to do? return latest, most likely, but this shouldnt
            happened
            """
    else:
        base_obj = None

    scan = Scan.create_scan(scan_type=scan_type, nvr=nvr, task_id=task_id,
                            tag=tag_obj, base=base_obj, username=username)

    options['scan_id'] = scan.id
    task = Task.objects.get(id=task_id)
    task.args = options
    task.save()


def finish_scanning(scan_id):
    size = run_diff(scan_id)

    scan = Scan.objects.get(id=scan_id)
    scan.set_scanner()

    if scan.is_errata_scan():
        if size is None or size == 0:
            scan.state = SCAN_STATES['PASSED']
        else:
            scan.state = SCAN_STATES['NEEDS_INSPECTION']
    elif scan.is_user_scan():
        scan.state = SCAN_STATES['FINISHED']
    scan.save()