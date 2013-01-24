# -*- coding: utf-8 -*-

import brew
import koji
import os
import re

__all__ = (
    "verify_brew_koji_build",
    "verify_mock",
)


# took this directly from koji source
# <koji_git_repo>/koji/__init__.py:153
KOJI_BUILD_STATES = (
    'BUILDING',
    'COMPLETE',
    'DELETED',
    'FAILED',
    'CANCELED',
)


def verify_build_exists(build, url, builder):
    """
    Verify if build exists
    """
    proxy_object = builder.ClientSession(url)
    try:
        # getBuild XML-RPC call is defined here: ./hub/kojihub.py:3206
        returned_build = proxy_object.getBuild(build)
    except brew.GenericError:
        return False
    except koji.GenericError:
        return False
    if returned_build is None:
        return False
    if 'state' in returned_build and \
            returned_build['state'] != KOJI_BUILD_STATES.index('COMPLETE'):
        return False
    return True


def verify_brew_koji_build(build, brew_url, koji_url):
    """
    Verify if brew or koji build exists
    """
    srpm = os.path.basename(build)  # strip path if any
    if srpm.endswith(".src.rpm"):
        srpm = srpm[:-8]

    dist_tag = re.search('.*-.*-(.*)', srpm).group(1)

    error_template = "Build %s does not exist in koji nor in brew, or has its \
files deleted, or did not finish successfully." % build

    koji_build_exists = True
    if 'fc' in dist_tag:
        koji_build_exists = verify_build_exists(srpm, koji_url, koji)
        if koji_build_exists:
            return None
    brew_build_exists = verify_build_exists(srpm, brew_url, brew)
    if not brew_build_exists and not koji_build_exists:
        return error_template
    elif not brew_build_exists:
        koji_build_exists = verify_build_exists(srpm, koji_url, koji)
        if not brew_build_exists and not koji_build_exists:
            return error_template
        else:
            return None
    else:
        return None


def verify_mock(mock, hub):
    mock_conf = hub.mock_config.get(mock)
    if not mock_conf:
        return "Unknown mock config: %s" % mock_conf
    if not mock_conf["enabled"]:
        return "Mock config is not enabled: %s" % mock_conf
    return None