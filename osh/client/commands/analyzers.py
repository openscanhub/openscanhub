# -*- coding: utf-8 -*-

from __future__ import absolute_import

import six


def check_analyzers(proxy, analyzers_list):
    result = proxy.scan.check_analyzers(analyzers_list)

    if isinstance(result, six.string_types):
        raise RuntimeError(str(result))
