# -*- coding: utf-8 -*-

from __future__ import absolute_import

import datetime
import logging
import re
import types

import six

from . import stattypes
from .models import StatResults, StatType

logger = logging.getLogger(__name__)


def get_last_stat_result(stat_type, release=None):
    if release:
        result = StatResults.objects.filter(stat=stat_type, release=release)
    else:
        result = StatResults.objects.filter(stat=stat_type)
    if result:
        return result.latest()


def get_mapping():
    """
    Return mapping between statistical function and its properties:
        { function: (tag, short_comment, comment, group, order), }
    """
    mapping = {}
    for binding_name in dir(stattypes):
        binding = getattr(stattypes, binding_name)
        if isinstance(binding, types.FunctionType) and\
                binding.__name__.startswith('get_'):
            doc = re.split('\n\\s*\n', binding.__doc__.strip())

            mapping[binding] = (binding.__name__[4:].upper(),
                                doc[0].strip(), doc[1].strip(),
                                binding.group, binding.order,
                                )
    return mapping


def create_stat_result(key, value, release=None):
    """
    Helper function that stores statistical result. If the result is same as
     in previous run, do not store it
    """
    stat_type = StatType.objects.get(key=key)
    last_stat = get_last_stat_result(stat_type, release)
    if not value:
        value = 0
    if not last_stat or last_stat.value != value:
        s = StatResults()
        s.stat = stat_type
        s.value = value
        if release is not None:
            s.release = release
        s.save()


def update():
    """
    Refresh statistics data.
    """
    logger.info('Update statistics.')
    for func, desc in six.iteritems(get_mapping()):
        stat_data = func()
        if isinstance(stat_data, int):
            create_stat_result(desc[0], stat_data)
        elif isinstance(stat_data, dict):
            for s in stat_data:
                create_stat_result(desc[0], stat_data[s], s)


def display_values(stat_type, release=None):
    if release:
        results = StatResults.objects.filter(stat=stat_type, release=release)
    else:
        results = StatResults.objects.filter(stat=stat_type)
    if not results:
        return {datetime.datetime.now(): 0}
    tmp = {}
    for result in results.order_by('-date'):
        tmp[result.date] = result.value
    return tmp
