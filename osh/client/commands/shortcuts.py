# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import os
import re
import sys
from urllib.error import HTTPError
from urllib.request import urlretrieve
from xmlrpc.client import Fault

import koji


def check_analyzers(proxy, analyzers_list):
    result = proxy.scan.check_analyzers(analyzers_list)
    if isinstance(result, str):
        raise RuntimeError(result)


def verify_build_exists(nvr, profile):
    """
    Verify if build exists
    """
    try:
        cfg = koji.read_config(profile)
    except koji.ConfigurationError as e:
        print('koji:', e, file=sys.stderr)
        return False

    proxy_object = koji.ClientSession(cfg['server'])
    try:
        # getBuild XML-RPC call is defined here: ./hub/kojihub.py:3206
        build = proxy_object.getBuild(nvr)
    except koji.GenericError:
        return False

    if build is None:
        return False

    # module metadata builds are not supported
    if build['extra'] is not None and 'typeinfo' in build['extra'] and \
            'module' in build['extra']['typeinfo']:
        return False

    return build.get('state') == koji.BUILD_STATES['COMPLETE']


def verify_koji_build(build, profiles):
    """
    Verify if brew or koji build exists
    """
    srpm = os.path.basename(build)  # strip path if any
    if srpm.endswith(".src.rpm"):
        srpm = srpm[:-8]

    # Get dist tag
    match = re.search('.*-.*-(.*)', srpm)
    if not match:
        return f'Invalid N-V-R: {srpm}'
    dist_tag = match[1]

    # Parse Koji profiles
    koji_profiles = profiles.split(',')
    if '' in koji_profiles:
        return f'Koji profiles could not be parsed properly: {koji_profiles}'

    # Use brew first unless fc is in the dist tag.
    # In that case, start with Fedora Koji.
    if 'fc' in dist_tag and 'brew' == koji_profiles[0]:
        koji_profiles.reverse()

    if any(verify_build_exists(build, p) for p in koji_profiles):
        return None

    return f"Build {build} does not exist in {koji_profiles}, is a module " +\
        "metadata build, has its files deleted, or did not finish successfully."


def verify_mock(mock, hub):
    mock_conf = hub.mock_config.get(mock)
    if not mock_conf:
        return f"Mock config {mock} does not exist."
    if not mock_conf["enabled"]:
        return f"Mock config {mock} is not enabled."
    return None


def handle_perm_denied(e, parser):
    """DRY"""
    if 'PermissionDenied: Login required.' in e.faultString:
        parser.error('You are not authenticated. Please \
obtain Kerberos ticket or specify username and password.')
    raise


def _get_result_filename(task_args):
    """
    Obtains the NVR from the task arguments dictionary.

    If the task argument contain the 'result_filename' key, just use that.
    Otherwise, use the following rules:

    * MockBuild and VersionDiffBuild tasks use either the 'srpm_name' key
      for an SRPM build or the 'build/nvr' key for Brew builds.
    * ErrataDiffBuild uses the 'build' key and used 'brew_build' key in
      the past.
    """
    if 'result_filename' in task_args:
        return task_args['result_filename']

    if "srpm_name" in task_args:
        return task_args['srpm_name'].replace('.src.rpm', '')

    if "brew_build" in task_args:
        return task_args["brew_build"]

    nvr = task_args['build']
    if isinstance(nvr, dict):
        nvr = nvr['nvr']
    return nvr


def fetch_results(hub, dest, task_id):
    """Downloads results for the given task"""
    task_info = hub.scan.get_task_info(task_id)
    task_url = hub.client.task_url(task_id)

    # we need result_filename + '.tar.xz'
    tarball = _get_result_filename(task_info['args']) + '.tar.xz'

    # get absolute path
    dest_dir = os.path.abspath(dest if dest is not None else os.curdir)
    local_path = os.path.join(dest_dir, tarball)

    # task_url is url to task with trailing '/'
    url = f"{task_url}log/{tarball}?format=raw"

    print(f"Downloading {tarball}: ", file=sys.stderr, end="")
    try:
        urlretrieve(url, local_path)
    except HTTPError as e:
        print(e, file=sys.stderr)
        return False

    print("OK", file=sys.stderr)
    return True


def upload_file(hub, srpm, target_dir, parser):
    """Upload file to hub, catch PermDenied exception"""
    try:
        # returns (upload_id, err_code, err_msg)
        return hub.upload_file(os.path.expanduser(srpm), target_dir)
    except Fault as e:
        handle_perm_denied(e, parser)


def verify_scan_profile_exists(hub, profile_name):
    """Verify if scan profile exists"""
    profiles = hub.scan.list_profiles()
    if any(p["name"] == profile_name for p in profiles):
        return None
    return f"Scan profile {profile_name} does not exist."
