# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from collections import OrderedDict

from django import template

register = template.Library()


@register.filter(name='sort', is_safe=True)
def listsort(value):
    if isinstance(value, dict):
        new_dict = OrderedDict()
        key_list = list(value.keys())
        key_list.sort(reverse=True)
        for key in key_list:
            new_dict[key] = value[key]
        return new_dict.items()
