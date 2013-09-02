# -*- coding: utf-8 -*-


def check_analyzers(proxy, analyzers_list):
    result = proxy.scan.check_analyzers(analyzers_list)

    if isinstance(result, basestring):
        raise RuntimeError(str(result))
