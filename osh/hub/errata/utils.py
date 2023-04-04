import logging

from kobo.rpmlib import parse_nvr

logger = logging.getLogger(__name__)


def get_or_fail(key, data):
    """ Convenience function for retrieving data from dict """
    try:
        return data[key]
    except KeyError:
        logger.error("Key '%s' is missing from dict '%s'", key, data)
        raise RuntimeError("Key '%s' is missing from '%s'!" % (key, data))


def is_rebase(base, target):
    """ base, target -- NVRs """
    base_d = parse_nvr(base)
    target_d = parse_nvr(target)
    return target_d['version'] != base_d['version']
