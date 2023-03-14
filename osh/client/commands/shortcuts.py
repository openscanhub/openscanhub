import os
import re
from xmlrpc.client import Fault

import koji


def check_analyzers(proxy, analyzers_list):
    result = proxy.scan.check_analyzers(analyzers_list)
    if isinstance(result, str):
        raise RuntimeError(result)


def verify_build_exists(build, url):
    """
    Verify if build exists
    """
    proxy_object = koji.ClientSession(url)
    try:
        # getBuild XML-RPC call is defined here: ./hub/kojihub.py:3206
        returned_build = proxy_object.getBuild(build)
    except koji.GenericError:
        return False

    return returned_build is not None and \
        returned_build.get('state', None) == koji.BUILD_STATES['COMPLETE']


def verify_brew_koji_build(build, brew_url, koji_url):
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

    # Use brew first unless fc is in the dist tag.
    # In that case, start with Koji.
    urls = [brew_url, koji_url]
    if 'fc' in dist_tag:
        urls.reverse()

    if any(verify_build_exists(build, url) for url in urls):
        return None

    return f"Build {build} does not exist in koji nor in brew, or has its \
files deleted, or did not finish successfully."


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


def upload_file(hub, srpm, target_dir, parser):
    """Upload file to hub, catch PermDenied exception"""
    try:
        # returns (upload_id, err_code, err_msg)
        return hub.upload_file(os.path.expanduser(srpm), target_dir)
    except Fault as e:
        handle_perm_denied(e, parser)
