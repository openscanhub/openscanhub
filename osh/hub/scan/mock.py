# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

"""
Functions related to dynamic generation of mock configs
"""

import logging
import os
import re
import subprocess
import tempfile
import uuid

import koji
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_available_parent_target(koji_proxy, target):
    """
    returns the first usable parent build target, otherwise returns None
    """
    parents = koji_proxy.getFullInheritance(target)
    while parents:
        target = parents[0]['name']
        if koji_proxy.getBuildTarget(target):
            return target
        parents = koji_proxy.getFullInheritance(target)

    return None


def _get_build_method_build_tag(koji_proxy, nvr, target):
    """
    returns build tag name of the first usable parent build target for given
    task, otherwise returns None
    """
    # rawhide buildroot always points to latest future release which may be
    # too new for old builds
    if target == 'rawhide':
        tags = sorted(t['name'] for t in koji_proxy.listTags(nvr, pattern='f*'))
        # use lowest 'f*' tag
        target = tags[0] if tags else None

    # try to handle removed side tags
    if target is not None and '-side' in target and koji_proxy.getTag(target) is None:
        target = target[:target.index('-side')]
        if koji_proxy.getTag(target):
            return target
        raise RuntimeError(f"Tag '{target}' of '{nvr}' is not available!")

    # handle the case if the target repo is no longer available
    if target is not None and koji_proxy.getBuildTarget(target) is None:
        # try to use the closest available parent (e.g. for merged side tags)
        target = _get_available_parent_target(koji_proxy, target)

    if target is None:
        return

    # get build tag name (build tag seems to always contain the release version)
    return koji_proxy.getBuildTarget(target)['build_tag_name']


def _get_module_build_tag(koji_proxy, task_id):
    """
    returns build tag name of the first regular external build target for given
    modular task
    """
    buildtag_id = None
    for child_id in koji_proxy.getTaskDescendents(task_id, request=True):
        child = koji_proxy.getTaskInfo(child_id, request=True)

        # skip non-buildArch tasks
        if child['method'] != 'buildArch':
            continue

        # parse buildtag_id from task parameters
        params = koji.parse_task_params(child['method'], child['request'])
        if 'root' not in params:
            # should not happen
            continue

        buildtag_id = params['root']
        break

    # get buildtag
    if buildtag_id is None:
        raise RuntimeError(f'Could not determine buildroot ID for task "{task_id}"')
    buildtag = koji_proxy.getTag(buildtag_id)

    # get external build repo
    repos = koji_proxy.getExternalRepoList(buildtag)
    if len(repos) != 1:
        raise RuntimeError('FIXME: Module builds with more or none external repos not implemented!')
    ext_repo_name = repos[0]['external_repo_name']

    # convert external repo to regular build tag
    assert ext_repo_name.endswith('-repo'), f'External repo name "{ext_repo_name}" does not end with "-repo"!'
    return ext_repo_name[:-5]


def _get_build_arches(koji_proxy, task_id):
    """
    returns all arches available for given build
    """
    arches = []
    for child_id in koji_proxy.getTaskDescendents(task_id, request=True):
        child = koji_proxy.getTaskInfo(child_id, request=True)
        if child['method'] == 'buildArch' and child['arch'] != 'noarch':
            arches.append(child['arch'])

    # noarch tasks can be built anywhere
    return arches or koji_proxy.getAllArches()


def _get_tag_specific_config(target):
    """
    returns build tag specific mock configuration which should be appended to
    the generated mock config
    """
    # CentOS Stream
    match = re.search(r'c(\d+)s', target)
    if match is not None:
        return "config_opts['use_bootstrap_image'] = True\n" \
               f"config_opts['releasever'] = '{match[1]}'\n" \
               f"config_opts['bootstrap_image'] = 'quay.io/centos/centos:stream{match[1]}'\n"

    # Fedora
    match = re.search(r'f(\d+)', target)
    if match is not None:
        return "config_opts['use_bootstrap_image'] = True\n" \
               f"config_opts['releasever'] = '{match[1]}'\n" \
               f"config_opts['bootstrap_image'] = 'registry.fedoraproject.org/fedora:{match[1]}'\n"

    # RHEL
    match = re.search(r'rhel-?(\d+)', target)
    if match is not None:
        return "config_opts['use_bootstrap_image'] = True\n" \
               f"config_opts['releasever'] = '{match[1]}'\n" \
               f"config_opts['bootstrap_image'] = 'registry.access.redhat.com/ubi{match[1]}/ubi'\n"

    # fallback
    return "config_opts['use_bootstrap_image'] = False\n"


def _create_mock_config(tag, arch, koji_profile, dest_dir):
    """
    creates a single mock config for given tag and architecture and stores it
    in given directory
    """
    p = subprocess.run(['koji', '-p', koji_profile, 'mock-config', '--latest',
                        '--arch', arch, '--tag', tag],
                       check=True, stdout=subprocess.PIPE)
    contents = p.stdout.decode()

    # add extra repos
    matched_repos = [repo for regex, repo
                     in getattr(settings, 'MOCK_AUTO_EXTRA_REPOS', {}).items()
                     if re.search(regex, tag)]
    extra_repos = '\n'.join(matched_repos).replace('\n', '\\n')
    contents = contents.replace("[main]", extra_repos + '\\n\\n[main]')

    # use randomly generated root directory name
    contents = re.sub(r"(config_opts\['root'\] = '[^']*)'",
                      fr"\1-{uuid.uuid4()}'", contents)

    with open(os.path.join(dest_dir, f'mock-{arch}.cfg'), 'w') as f:
        f.write(contents)
        f.write(_get_tag_specific_config(tag))


def generate_mock_configs(nvr, koji_profile):
    """
    returns a path to temporary directory with generated mock configs
    for given NVR
    """
    tmpdir = tempfile.mkdtemp()

    # retrieve the build
    cfg = koji.read_config(koji_profile)
    koji_proxy = koji.ClientSession(cfg['server'])
    build = koji_proxy.getBuild(nvr)

    # retrieve task parameters
    task = koji_proxy.getTaskInfo(build['task_id'], request=True)
    method = task['method']
    params = koji.parse_task_params(method, task['request'])

    # parse build tag name from task parameters
    if method == 'build':
        # obtain module build target
        if 'mbs_module_target' in params['opts']:
            tag = _get_module_build_tag(koji_proxy, task['id'])
        else:
            tag = _get_build_method_build_tag(koji_proxy, nvr, params['target'])
    elif method == 'buildContainer':
        raise RuntimeError('Generation of mock configs is unsupported for container builds!')
    elif method == 'wrapperRPM':
        tag = params['build_target']['build_tag_name']
    # TODO: add other methods
    else:
        raise RuntimeError(f'No build target for "{nvr}" available!')

    # generate a config for every built arch
    logger.debug(f'Generating mock configs for build tag "{tag}"')
    for arch in _get_build_arches(koji_proxy, task['id']):
        _create_mock_config(tag, arch, koji_profile, tmpdir)

    return tmpdir
