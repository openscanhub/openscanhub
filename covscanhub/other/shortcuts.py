# -*- coding: utf-8 -*-

import os

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from covscanhub.other.django_version import django_version_ge
if django_version_ge('1.10.0'):
    from django.urls import reverse
else:
    from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
import koji

from covscanhub.scan.models import MockConfig, Tag
from covscanhub.other.exceptions import BrewException
import six


__all__ = (
    'add_link_field',
    'get_mock_by_name',
    'check_brew_build',
    'check_and_create_dirs',
    'get_tag_by_name',
    'get_or_none',
)


def add_link_field(target_model=None, field='', app='', field_name='link',
                   link_text=six.text_type, field_label=''):
    def add_link(cls):
        reverse_name = target_model or cls.model.__name__.lower()

        def link(self, instance):
            app_name = app or instance._meta.app_label
            reverse_path = "admin:%s_%s_change" % (app_name, reverse_name)
            link_obj = getattr(instance, field, None)
            if not link_obj:
                return mark_safe('None')
            url = reverse(reverse_path, args=(link_obj.id,))
            return mark_safe("<a href='%s'>%s</a>" %
                             (url, link_text(link_obj)))
        link.allow_tags = True
        link.short_description = field_label or (reverse_name + ' link')
        setattr(cls, field_name, link)
        #cls.link = link
        cls.readonly_fields = list(getattr(cls, 'readonly_fields', [])) + \
            [field_name]
        return cls
    return add_link


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
    brew_proxy = koji.ClientSession(settings.BREW_HUB)
    build = brew_proxy.getBuild(srpm)
    if build is None:
        raise BrewException('Brew build %s does not exist' % srpm)
    return srpm


def check_and_create_dirs(directory):
    if not os.path.isdir(directory):
        try:
            os.makedirs(directory, mode=0o755)
        except OSError as ex:
            if ex.errno != 17:
                raise
