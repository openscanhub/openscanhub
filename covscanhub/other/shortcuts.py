# -*- coding: utf-8 -*-

from covscanhub.scan.models import MockConfig
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

import brew

def get_mock_by_name(name):
    try:
        conf = MockConfig.objects.get(name=name)
    except:
        raise ObjectDoesNotExist("Unknown mock config: %s" % name)
    if not conf.enabled:
        raise RuntimeError("Mock config is disabled: %s" % conf)


def check_brew_build(name):
    if name.endswith(".src.rpm"):
        srpm = name[:-8]
    else:
        srpm = name
    # XXX: hardcoded
    brew_proxy = brew.ClientSession(settings.BREW_HUB)
    try:
        brew_proxy.getBuild(srpm)
    except brew.GenericError:
        raise RuntimeError("Brew build of package %s does not exist" % name)
    return srpm