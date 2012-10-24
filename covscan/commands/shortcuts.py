# -*- coding: utf-8 -*-

import brew
import os


__all__ = (
    'verify_brew_build',
    'verify_mock',
)


def verify_brew_build(build, brew_url):
    srpm = os.path.basename(build)  # strip path if any
    if srpm.endswith(".src.rpm"):
        srpm = srpm[:-8]
    brew_proxy = brew.ClientSession(brew_url)
    try:
        brew_proxy.getBuild(srpm)
    except brew.GenericError:
        return "Build does not exist in brew: %s" % srpm
    return None


def verify_mock(mock, hub):
    mock_conf = hub.mock_config.get(mock)
    if not mock_conf:
        return "Unknown mock config: %s" % mock_conf
    if not mock_conf["enabled"]:
        return "Mock config is not enabled: %s" % mock_conf
    return None