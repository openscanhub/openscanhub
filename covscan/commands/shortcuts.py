# -*- coding: utf-8 -*-

import brew
import koji
import os
import re

__all__ = (
    "verify_brew_koji_build",
    "verify_mock",
)


def verify_build_exists(build, url, builder):
    """
    Verify if build exists
    """
    proxy_object = builder.ClientSession(url)
    try:
        returned_build = proxy_object.getBuild(build)
    except brew.GenericError:
        return 'Build %s does not exist' % build
    except koji.GenericError:
        return 'Build %s does not exist' % build
    if returned_build is None:
        return 'Build %s does not exist' % build
    return None


def verify_brew_koji_build(build, brew_url, koji_url):
    """
    Verify if brew or koji build exists
    """
    srpm = os.path.basename(build)  # strip path if any
    if srpm.endswith(".src.rpm"):
        srpm = srpm[:-8]

    dist_tag = re.search('.*-.*-(.*).', srpm).group(1)

    if 'fc' in dist_tag:
        error_line = verify_build_exists(srpm, koji_url, koji)
        if not error_line:
            return None
    error_line = verify_build_exists(srpm, brew_url, brew)
    if error_line:
        return verify_build_exists(srpm, koji_url, koji)
    else:
        return None


def verify_mock(mock, hub):
    mock_conf = hub.mock_config.get(mock)
    if not mock_conf:
        return "Unknown mock config: %s" % mock_conf
    if not mock_conf["enabled"]:
        return "Mock config is not enabled: %s" % mock_conf
    return None