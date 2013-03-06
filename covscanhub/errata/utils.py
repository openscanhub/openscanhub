# -*- coding: utf-8 -*-

import yum
import brew
import koji
#import itertools

#from pprint import pprint

from kobo.rpmlib import parse_nvr
from kobo.hub.models import Task, TASK_STATES

from django.conf import settings

from covscanhub.scan.models import SCAN_TYPES, Scan
from covscanhub.other.shortcuts import check_and_create_dirs


__all__ = (
    "depend_on",
    "spawn_scan_task",
    "_spawn_scan_task",
)


def _spawn_scan_task(d):
    """
    parent method that actually creates Task and Scan

    @type d: dict
    """
    task_id = Task.create_task(
        owner_name=d['task_user'],
        label=d['task_label'],
        method=d['method'],
        args={},  # I want to add scan's id here, so I update it later
        comment=d['comment'],
        state=TASK_STATES["CREATED"],
        priority=d['priority'],
        parent_id=d.get('parent_id', None),
    )
    task_dir = Task.get_task_dir(task_id)

    check_and_create_dirs(task_dir)

    scan = Scan.create_scan(scan_type=d['scan_type'], nvr=d['target'],
                            username=d['package_owner'],
                            tag=d['tag'], package=d['package'],
                            enabled=d['scan_enabled'])
    return task_id, scan

##########
# SPAWNING
##########


def spawn_newpkg(d):
    d.update((
        ('method', 'ErrataDiffBuild'),
        ('scan_type', SCAN_TYPES['NEWPKG']),
    ), )
    return _spawn_scan_task(d)


def spawn_rebase(d):
    d.update((
        ('method', 'ErrataDiffBuild'),
        ('scan_type', SCAN_TYPES['REBASE']),
    ), )
    return _spawn_scan_task(d)


def spawn_classic(d):
    d.update((
        ('method', 'ErrataDiffBuild'),
        ('scan_type', SCAN_TYPES['ERRATA']),
    ), )
    return _spawn_scan_task(d)


def is_rebase(base, target_d):
    base_d = parse_nvr(base)
    return target_d['version'] == base_d['version']


def spawn_scan_task(d, target):
    """
    Figure out scan type and create scan and task models
    Exported method

    @type d: dict
    @type target: dict (save one parse_nvr call)
    """
    d['scan_enabled'] = True
    if d['base'].lower() == 'new_package':
        return spawn_newpkg(d)
    elif is_rebase(d['base'], target):
        return spawn_rebase(d)
    else:
        return spawn_classic(d)

###########
# PKG QUERY
###########


def depend_on(package_name, dependency):
    """
    TODO: check dependency from other side: check what depends on glibc and
          find out if `package_name` is in there, because this might not work
          for parent meta packages etc.
    """
    yb = yum.YumBase()
    yb.preconf.debuglevel = 0
    yb.setCacheDir()
    pkgs = yb.pkgSack.returnNewestByNameArch(patterns=[package_name])
    for pkg in pkgs:
        # alternative: for req in pkg.requires:
        for req in pkg.returnPrco('requires'):
            if req[0].startswith(dependency):
                return True
    return False

######
# BREW
######


def get_build_tuple(nvr):

    try:
        s = brew.ClientSession(settings.BREW_HUB)
    except ImportError:
        s = brew.ClientSession("http://brewhub.devel.redhat.com/brewhub")

    build = s.getBuild(nvr)
    task = s.getTaskInfo(build['task_id'], request=True)
    target_name = task['request'][1]
    target = s.getBuildTarget(target_name)
    return (s, s.getRepo(target['build_tag_name']), target, task)


def retrieve_mock_for_build(nvr):
    # http://download.devel.redhat.com/brewroot/repos/rhel-7.0-build/574607/x86_64
    # http://download.englab.brq.redhat.com/brewroot/
    # http://download.eng.brq.redhat.com/brewroot/
    # download-01.eng.brq.redhat.com
    TOP_URL = "http://download.devel.redhat.com/brewroot"

    build_tuple = get_build_tuple(nvr)
    repo, target = build_tuple[1:3]
    mock = koji.genMockConfig(target['build_tag_name'],
                              "x86_64",
                              tag_name=target['build_tag_name'],
                              repoid=repo['id'],
                              topurl=TOP_URL)
    return mock


def get_overrides(nvr):
    s, repo, target, task = get_build_tuple(nvr)

    child_tasks = s.getTaskChildren(task['id'], request=True)
    for t in child_tasks:
        if t['method'] == 'buildArch' and t['arch'] == 'x86_64':
            build_task = t
#    repo_states = brew.REPO_STATES
    request = build_task['request']

    repo_id = request[4]['repo_id']
    old_repo = s.repoInfo(repo_id)

    new_repo = s.getRepo(target['build_tag'])

    old_builds = s.listTagged(target['build_tag'],
                              latest=True,
                              inherit=True,
                              event=old_repo['create_event'])

    new_builds = s.listTagged(target['build_tag'],
                              latest=True,
                              inherit=True,
                              event=new_repo['create_event'])
    old_packages = set([(o['package_name'], o['nvr']) for o in old_builds])
    new_packages = [(o['package_name'], o['nvr']) for o in new_builds]

    # in new, not in old
    diff1 = [o for o in new_packages if o not in old_packages]
    # in old, not in new
    diff2 = [o for o in old_packages if o not in new_packages]

    return diff2


if __name__ == '__main__':
    import sys
    #print depend_on(sys.argv[1], sys.argv[2])
    #print retrieve_mock_for_build(sys.argv[1])
    get_overrides(sys.argv[1])
