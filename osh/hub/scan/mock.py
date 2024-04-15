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

    # handle the case if the target repo is no longer available
    if target is not None and koji_proxy.getBuildTarget(target) is None:
        # try to use the closest available parent (e.g. for merged side tags)
        target = _get_available_parent_target(koji_proxy, target)

    if target is None:
        return

    # get build tag name (build tag seems to always contain the release version)
    return koji_proxy.getBuildTarget(target)['build_tag_name']


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
        return f"config_opts['releasever'] = '{match[1]}'\n" \
               f"config_opts['bootstrap_image'] = 'quay.io/centos/centos:stream{match[1]}'\n"

    # Fedora
    match = re.search(r'f(\d+)', target)
    if match is not None:
        return f"config_opts['releasever'] = '{match[1]}'\n" \
               f"config_opts['bootstrap_image'] = 'registry.fedoraproject.org/fedora:{match[1]}'\n"

    # RHEL
    match = re.search(r'rhel-?(\d+)', target)
    if match is not None:
        return f"config_opts['releasever'] = '{match[1]}'\n" \
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

    # FIXME: remove when dnf5 is usable with mock
    if 'dnf5' in contents:
        contents = contents.replace('dnf5', 'dnf')

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
        tag = _get_build_method_build_tag(koji_proxy, nvr, params['target'])
    # TODO: add other methods
    else:
        raise RuntimeError(f'No build target for "{nvr}" available!')

    # generate a config for every built arch
    logger.debug(f'Generating mock configs for build tag "{tag}"')
    for arch in _get_build_arches(koji_proxy, task['id']):
        _create_mock_config(tag, arch, koji_profile, tmpdir)

    return tmpdir