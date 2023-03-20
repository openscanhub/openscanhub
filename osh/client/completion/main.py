#!/usr/bin/env python3

import argparse
import datetime
import os
import pickle

from kobo.client import HubProxy

from osh.common.conf import get_config_dict

CACHE_PATH_PREFIX = '.cache/osh'


def get_can_path():
    """
    Return path to can with pickles
    """
    cache_path = os.path.join(os.path.expanduser('~'), CACHE_PATH_PREFIX)
    os.makedirs(cache_path, exist_ok=True)
    return os.path.join(cache_path, 'bash_compl.pickle')


def get_configs_from_hub():
    """
    Return enabled mockconfigs from hub
    """
    conf = get_config_dict(config_env="OSH_CLIENT_CONFIG_FILE",
                           config_default="/etc/osh/client.conf")
    if not conf:
        return []

    hub = HubProxy(conf)
    return [x['name'] for x in hub.mock_config.all() if x['enabled']]


def write_configs():
    """
    write configs which were retieved from hub to pickle can
    """
    can_path = get_can_path()
    configs = get_configs_from_hub()
    with open(can_path, 'wb') as fd:
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

    print(*enabled_configs)


def main(args):
    if 'mock-configs' == args.action:
        list_enabled_mock_configs()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['mock-configs'],
                        help='select what should be completed')

    main(parser.parse_args())
