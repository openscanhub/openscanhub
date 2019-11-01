# -*- coding: utf-8 -*-

from django import template
from django.utils.safestring import mark_safe
from django.utils.datastructures import SortedDict
import six

register = template.Library()


@register.filter(name='sort')
def listsort(value):
    if isinstance(value, dict):
        new_dict = SortedDict()
        key_list = list(value.keys())
        key_list.sort(reverse=True)
        for key in key_list:
            new_dict[key] = value[key]
        return six.iteritems(new_dict)
listsort.is_safe = True