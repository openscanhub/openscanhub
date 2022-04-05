# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import

import six

import re

from covscancommon.utils.conf import get_conf

__all__ = (
    'extract_cim_data',
)


def set_defaults(cim_dict):
    """set defualt options from configuration files if they are not provided"""
    conf = get_conf()
    conf_cim_data = conf.get_cim_data()

    for key, value in six.iteritems(cim_dict):
        if value is None:
            cim_dict[key] = conf_cim_data[key]


def extract_cim_data(s):
    if len(s) == 0:
        cim_dict = {
            'user': None,
            'passwd': None,
            'server': None,
            'port': None,
            'stream': None,
        }
    else:
        cim_dict = verify_cim_string(s)

    if cim_dict['server'] is None or cim_dict['stream'] is None or \
            cim_dict['user'] is None:
        set_defaults(cim_dict)
    return cim_dict


def verify_cim_string(s):
    """
    Verify if provided CIM string is valid:
        user:passwd@server:port/stream
    Valid options are:
        user:passwd
        user:passwd@server:port
        user:passwd@server:port/stream
    """
    # Kamil's pattern ^([^@:]+):([^@]+)(?:@([^:/]+)(?::([^/]+)(?:/(.+))?)?)?$
    pattern = "^(?P<user>[^@:]+):(?P<passwd>[^@]+?)\
(@(?P<server>[^:/]+):(?P<port>\d+)(/(?P<stream>.+))?)?$"
    m = re.match(pattern, s)
    if m:
        return m.groupdict()
    else:
        raise RuntimeError("%s is an invalid string" % s)

if __name__ == '__main__':
    test_data = [
        # string, expected result
        ('user:passwd@server:1234/stream', {
            'user': 'user',
            'passwd': 'passwd',
            'server': 'server',
            'port': '1234',
            'stream': 'stream',
        }),
        ('user:passwd@server:4567', {
            'user': 'user',
            'passwd': 'passwd',
            'server': 'server',
            'port': '4567',
            'stream': None,
        }),
        ('user:passwd', {
            'user': 'user',
            'passwd': 'passwd',
            'server': None,
            'port': None,
            'stream': None,
        }),
        ('admin:xxxxxx@cov01.lab.eng.brq.redhat.com:8080', {
            'user': 'admin',
            'passwd': 'xxxxxx',
            'server': 'cov01.lab.eng.brq.redhat.com',
            'port': '8080',
            'stream': None,
        }),
    ]
    invalid_strings = [
        "admin:pswd@fail.hostname.com",
    ]
    for entry in test_data:
        try:
            to_verify = verify_cim_string(entry[0])
            assert to_verify == entry[1]
        except AssertionError:
            print('Assert error!', entry[0], "is not a valid string, \
expected:", entry[1], 'got: ', to_verify)

    for entry in invalid_strings:
        try:
            result = verify_cim_string(entry)
            raise AssertionError
        except AssertionError:
            print(entry, 'is invalid string and should have been denied!', \
                result)
        except RuntimeError:
            pass

