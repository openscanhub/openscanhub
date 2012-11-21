# -*- coding: utf-8 -*-

from django import template
from django.utils.safestring import mark_safe
from django.utils.datastructures import SortedDict

register = template.Library()


@register.filter(name='sort')
def listsort(value):
    if isinstance(value, dict):
        new_dict = SortedDict()
        key_list = value.keys()
        key_list.sort()
        for key in key_list:
            new_dict[key] = value[key]
        return new_dict
listsort.is_safe = True