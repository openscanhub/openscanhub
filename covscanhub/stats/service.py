# -*- coding: utf-8 -*-


import stattypes
import types
from models import StatType, StatResults


def get_mapping():
    mapping = {}
    for binding_name in dir(stattypes):
        binding = getattr(stattypes, binding_name)
        if isinstance(binding, types.FunctionType) and\
                binding.__name__.startswith('get_'):
            mapping[binding] = (binding.__name__[4:].upper(),
                                binding.__doc__.strip())
    return mapping


def update():
    """
    Update statistics data.
    """
    for func, desc in get_mapping().iteritems():
        s = StatResults()
        st, created = StatType.objects.get_or_create(key=desc[0],
                                                     comment=desc[1])
        s.stat = st
        s.value = func()
        s.save()            