# -*- coding: utf-8 -*-

from covscanhub.scan.models import MockConfig, Tag
from covscanhub.other.exceptions import BrewException
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

import brew
import os


__all__ = (
    'get_mock_by_name',
    'check_brew_build',
    'check_and_create_dirs',
    'get_tag_by_name',
)


def get_mock_by_name(name):
    try:
        conf = MockConfig.objects.get(name=name)
    except:
        raise ObjectDoesNotExist("Unknown mock config: %s" % name)
    if not conf.enabled:
        raise RuntimeError("Mock config is disabled: %s" % conf)
    return conf


def get_tag_by_name(name):
    try:
        tag = Tag.objects.get(name=name)
    except:
        raise ObjectDoesNotExist("Unknown tag config: %s" % name)
    if not tag.mock.enabled:
        raise RuntimeError("Mock config is disabled: %s" % tag.mock)
    return tag


def check_brew_build(name):
    if name.endswith(".src.rpm"):
        srpm = name[:-8]
    else:
        srpm = name
    brew_proxy = brew.ClientSession(settings.BREW_HUB)
    build = brew_proxy.getBuild(srpm)
    if build is None:
        raise BrewException('Brew build %s does not exist' % srpm)
    return srpm


def check_and_create_dirs(directory):
    if not os.path.isdir(directory):
        try:
            os.makedirs(directory, mode=0755)
        except OSError, ex:
            if ex.errno != 17:
                raise