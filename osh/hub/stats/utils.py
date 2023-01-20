# -*- coding: utf-8 -*-


def stat_function(index, group_name):
    def decorator(function):
        function.order = index
        function.group = group_name
        return function
    return decorator
