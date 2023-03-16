#!/usr/bin/env python3

import datetime
import os
import pickle
import xmlrpc.client

from osh.common.utils.conf import get_conf, get_config_dict


def get_can_path():
    """
    Return path to can with pickles
    """
    return os.path.join(get_conf().get_conf_dir(), 'bash_compl.pickle')


def get_configs_from_hub():
    """
    Return enabled mockconfigs from hub
    """
    conf = get_config_dict(config_env="OSH_CLIENT_CONFIG_FILE",
                           config_default="/etc/osh/client.conf")
    if not conf:
        return []

    client = xmlrpc.client.ServerProxy(conf['HUB_URL'], allow_none=True)
    return [x for x in client.mock_config.all() if x['enabled']]


def write_configs():
    """
    write configs which were retieved from hub to pickle can
    """
    can_path = get_can_path()
    with open(can_path, 'wb') as fd:
        configs = get_configs_from_hub()
        pickle.dump(configs, fd)
    return configs


def list_enabled_mock_configs():
    """
    this function should be called from outside world
    """
    try:
        with open(get_can_path(), 'rb') as can:
            can_time = datetime.datetime.fromtimestamp(
                os.path.getmtime(get_can_path()))

            if can_time + datetime.timedelta(minutes=5) > datetime.datetime.now():
                enabled_configs = pickle.load(can)
            else:
                enabled_configs = write_configs()
    except OSError:
        enabled_configs = write_configs()
    for emc in enabled_configs:
        print(emc['name'])


def main():
    list_enabled_mock_configs()


if __name__ == "__main__":
    main()
