# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

"""
Functions related to dynamic generation of mock configs
"""

import logging
import os
import re
import subprocess

import koji

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


def _get_bootstrap_image(target):
    """
    returns all arches
    """
    # Fedora
    match = re.search(r'f(\d+)', target)
    if match is not None or 'rawhide' in target:
        label = match[1] if match is not None else 'rawhide'
        return f"config_opts['bootstrap_image'] = 'registry.fedoraproject.org/fedora:{label}'\n"

    # CentOS Stream
    match = re.search(r'c(\d+)s', target)
    if match is not None:
        return f"config_opts['bootstrap_image'] = 'quay.io/centos/centos:stream{match[1]}'\n"

    # RHEL
    match = re.search(r'rhel-?(\d+)', target)
    if match is not None:
        return f"config_opts['bootstrap_image'] = 'registry.access.redhat.com/ubi{match[1]}/ubi'\n"

    # fallback
    return "config_opts['use_bootstrap_image'] = False\n"


def generate_mock_configs(nvr, koji_profile, task_dir):
    # retrieve the original build target
    cfg = koji.read_config(koji_profile)
    proxy_object = koji.ClientSession(cfg['server'])
    build = proxy_object.getBuild(nvr)
    task = proxy_object.getTaskInfo(build['task_id'], request=True)
    params = koji.parse_task_params(task['method'], task['request'])
    target = params['target']

    # handle the case if the target repo is no longer available
    if target is not None and proxy_object.getBuildTarget(target) is None:
        logger.debug(f'"{nvr}" was built in target "{target}" which is no longer available')

        # try to use the closes available parent (e.g. for merged side tags)
        target = _get_available_parent_target(proxy_object, target)

    if target is None:
        # FIXME: add actual error handling
        logger.error(f'No build target for "{nvr}" available')
        return

    # generate a config for every built arch
    logger.debug(f'Generating mock configs for build target "{target}"')
    for arch in _get_build_arches(proxy_object, task['id']):
        p = subprocess.run(['koji', '-p', koji_profile, 'mock-config',
                            '--arch', arch, '--latest', '--target', target],
                           check=True, stdout=subprocess.PIPE)
        contents = p.stdout.decode()

        with open(os.path.join(task_dir, f'mock-{arch}.cfg'), 'w') as f:
            f.write(contents)
            f.write(_get_bootstrap_image(target))
