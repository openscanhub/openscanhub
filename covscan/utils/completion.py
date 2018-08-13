#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

import os
import xmlrpclib
import datetime
import cPickle as pickle
from conf import get_conf


def get_can_path():
    """
    Return path to can with pickles
    """
    return os.path.join(get_conf().get_conf_dir(), 'bash_compl.pickle')


def get_configs_from_hub():
    """
    Return enabled mockconfigs from hub
    """
    # FIXME: load this URL from /etc/covscan.conf instead
    rpc_url = "https://cov01.lab.eng.brq.redhat.com/covscanhub/xmlrpc/client/"
    client = xmlrpclib.ServerProxy(rpc_url, allow_none=True)
    return filter(lambda x: x['enabled'], client.mock_config.all())


def write_configs():
    """
    write configs which were retieved from hub to pickle can
    """
    can_path = get_can_path()
    fd = open(can_path, 'w')
    configs = get_configs_from_hub()
    pickle.dump(configs, fd)
    return configs


def list_enabled_mock_configs():
    """
    this function should be called from outside world
    """
    try:
        can = open(get_can_path(), 'r')
    except IOError:
        enabled_configs = write_configs()
    else:
        can_time = datetime.datetime.fromtimestamp(
            os.path.getmtime(get_can_path()))

        if can_time + datetime.timedelta(minutes=5) > datetime.datetime.now():
            enabled_configs = pickle.load(can)
        else:
            enabled_configs = write_configs()
    for emc in enabled_configs:
        print emc['name'],


def main():
    list_enabled_mock_configs()


if __name__ == "__main__":
    main()
