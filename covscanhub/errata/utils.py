# -*- coding: utf-8 -*-

import re
import yum
import koji
import logging

from kobo.rpmlib import parse_nvr
from kobo.hub.models import Task, TASK_STATES

from covscanhub.scan.models import SCAN_TYPES, Scan
from covscanhub.other.shortcuts import check_and_create_dirs

from django.conf import settings


__all__ = (
    "depend_on",
    "spawn_scan_task",
    "_spawn_scan_task",
)

logger = logging.getLogger(__name__)

try:
    s = koji.ClientSession(settings.BREW_HUB)
except (ImportError, NameError):
    s = koji.ClientSession("http://brewhub.devel.redhat.com/brewhub")


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
    return target_d['version'] != base_d['version']


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


def get_mocks_repo(mock_profile):
    """
    return repo acoording to $(grep "baseurl" /etc/mock/`mock_profile`)
    if there is only one, return string, else return list of repos
    """
    f = open('/etc/mock/%s.cfg' % mock_profile, 'r')
    urls = []
    pattern = re.compile(r'baseurl=([^\\\s]+)')
    with f:
        f.seek(0)
        for line in f:
            for match in pattern.finditer(line):
                if match.group(1):
                    urls.append(match.group(1).strip())
    if len(urls) == 1:
        return urls[0]
    else:
        return urls


def depend_on_brew(valid_rpms, dependency):
    """
    Check with brew if one of `valid_rpms[:]['name']` depends on `dependency`
    """
    def check_if_dep_match(item):
        try:
            dep_name = item['name']
        except KeyError:
            return False
        return dep_name.startswith(dependency)
    for rpm in valid_rpms:
        # get requires from brew, second arg is dependency type
        requires = s.getRPMDeps(valid_rpms[0]['id'], koji.DEP_REQUIRE)
        if filter(check_if_dep_match, requires):
            logger.info("depend_on_brew, %s depends on %s",
                        rpm['name'], dependency)
            return True
    logger.info("depend_on_brew, no RPM depends on %s", dependency)
    return False


def depend_on(nvr, dependency, mock_profile):
    """
    for q in `repoquery -s --alldeps --whatrequires libc.so*` ; do
       echo $q | rev | cut -d'-' -f3- | rev

    find out if binary packages built from `nvr` are dependant on `dependency`
    """
    # get build from brew
    build = s.getBuild(nvr)
    # list all binary packages built from srpm
    rpms = s.listRPMs(buildID=build['id'])
    # we do care only about x86_64
    valid_rpms = filter(lambda x: x['arch'] == 'x86_64', rpms)
    if not valid_rpms:
        logger.error("no valid RPMs for %s", nvr)
        return False

    # find out dependency using yum
    yb = yum.YumBase()
    yb.preconf.debuglevel = 0
    yb.setCacheDir()

    # get data only from mock profile's repo
    repo_url = get_mocks_repo(mock_profile)
    if repo_url:
        disabled_repos = []
        for repo in yb.repos.findRepos('*'):
            repo.disable()
            disabled_repos.append(repo)
        if isinstance(repo_url, list):
            counter = 1
            for url in repo_url:
                yb.add_enable_repo(
                    "%s_%d" % (mock_profile, counter),
                    baseurls=[url]
                )
                counter += 1
        elif isinstance(repo_url, basestring):
            yb.add_enable_repo(mock_profile, baseurls=[repo_url])
        ## check if repo is okay; if not, use default repositories
        #try:
        #    mock_repo.check()
        #except Exception:
        #    for repo in disabled_repos:
        #        repo.enable()
        #    mock_repo.disable()

    packages = [rpm['name'] for rpm in valid_rpms]
    try:
        pkgs = yb.pkgSack.returnNewestByNameArch(patterns=packages)
    except yum.Errors.PackageSackError, ex:
        # package was not found in repo, try brew instead
        logger.warning("depend_on, package not found in repo (%s) %s",
                       ex, packages)
        return depend_on_brew(valid_rpms, dependency)
    except Exception, ex:
        # there was some problem with search of package in repo using yum
        # use brew instead
        logger.warning("depend_on, yum exception %s, packages %s",
                       ex, packages)
        return depend_on_brew(valid_rpms, dependency)

    for pkg in pkgs:
        # alternative: for req in pkg.requires:
        for req in pkg.returnPrco('requires'):
            if req[0].startswith(dependency):
                logger.info("%s depends on %s", pkg.name, dependency)
                return True
    logger.info("%s do not depend on %s", packages, dependency)
    return False

######
# BREW
######


def get_build_tuple(nvr):

    global s

    build = s.getBuild(nvr)
    task = s.getTaskInfo(build['task_id'], request=True)
    target_name = task['request'][1]

    # this can be None
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


def test_depend_on():
    assert(depend_on('aspell-0.60.3-13', 'libc.so', 'rhel-5-x86_64'))
    assert(depend_on('redhat-release-5Server-5.10.0.2',
                     'libc.so', 'rhel-5-x86_64') is False)
    assert(depend_on('mysql55-mysql-5.5.31-9.el5',
                     'libc.so', 'rhel-5-x86_64'))
    assert(depend_on('mysql55-1-12.el5', 'libc.so', 'rhel-5-x86_64') is False)
    assert(depend_on('openldap-2.4.23-33.el6', 'libc.so', 'rhel-6-x86_64'))
    assert(depend_on('wget-1.11.4-4.el6', 'libc.so', 'rhel-6-x86_64'))
    assert(depend_on('hardlink-1.0-9.el6', 'libc.so', 'rhel-6-x86_64'))
    assert(depend_on('coreutils-8.4-5.el6', 'libc.so', 'rhel-6-x86_64'))
    assert(depend_on('libssh2-1.4.2-1.el6', 'libc.so', 'rhel-6-x86_64'))
    assert(depend_on('hypervkvpd-0-0.10.el6', 'libc.so', 'rhel-6-x86_64'))
    assert(depend_on('gnome-python2-desktop-2.28.0-5.el6',
                     'libc.so', 'rhel-6-x86_64'))


def test_get_mock_repo():
    print get_mocks_repo('rhel-6.5-x86_64')
    print get_mocks_repo('fedora-18-x86_64')
    print get_mocks_repo('rhel-7-x86_64')

if __name__ == '__main__':
    test_depend_on()
    test_get_mock_repo()
