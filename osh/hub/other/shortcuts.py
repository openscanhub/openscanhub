import os

import koji
from django.conf import settings
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from osh.hub.other.exceptions import BrewException


def add_link_field(target_model=None, field='', field_label=''):
    field_name = field + '_link'

    def add_link(cls):
        reverse_name = target_model or cls.model.__name__.lower()

        def link(self, instance):
            app_name = instance._meta.app_label
            reverse_path = f"admin:{app_name}_{reverse_name}_change"
            link_obj = getattr(instance, field, None)
            if not link_obj:
                return mark_safe('None')
            url = reverse(reverse_path, args=(link_obj.id,))
            return format_html("<a href='{}'>{}</a>",
                               url,
                               str(link_obj))
        link.short_description = field_label or (reverse_name + ' link')
        setattr(cls, field_name, link)
        # cls.link = link
        cls.readonly_fields = list(getattr(cls, 'readonly_fields', [])) + \
            [field_name]
        return cls
    return add_link


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
