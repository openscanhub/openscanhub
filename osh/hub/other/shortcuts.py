# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe


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
