def check_analyzers(proxy, analyzers_list):
    result = proxy.scan.check_analyzers(analyzers_list)
    if isinstance(result, str):
        raise RuntimeError(result)
