#!/usr/bin/env python3

import argparse
import os
import pickle
from datetime import datetime, timedelta

from kobo.client import HubProxy

from osh.common.conf import get_config_dict

CACHE_PATH_PREFIX = '.cache/osh'


def get_can_path(action):
    """
    Return path to can with pickles
    """
    cache_path = os.path.join(os.path.expanduser('~'), CACHE_PATH_PREFIX)
    os.makedirs(cache_path, exist_ok=True)
    return os.path.join(cache_path, f'bash_compl_{action}.pickle')


def connect_to_hub():
    """
    Return hub proxy object
    """
    conf = get_config_dict(config_env="OSH_CLIENT_CONFIG_FILE",
                           config_default="/etc/osh/client.conf")
    if not conf:
        return None

    return HubProxy(conf)


def fetch_analyzers(hub):
    """
    Return available analyzers from hub
    """
    return [x['cli_long_command'] for x in hub.scan.list_analyzers()]


def fetch_profiles(hub):
    """
    Return available profiles from hub
    """
    return [x['name'] for x in hub.scan.list_profiles()]


def fetch_mock_configs(hub):
    """
    Return enabled mock configs from hub
    """
    return [x['name'] for x in hub.mock_config.all() if x['enabled']]


def load_from_cache(action):
    """
    Try to load up to date data from the cache
    """
    can_path = get_can_path(action)

    try:
        with open(can_path, 'rb') as can:
            can_time = datetime.fromtimestamp(os.path.getmtime(can_path))
            if can_time + timedelta(minutes=5) > datetime.now():
                return pickle.load(can)
    except OSError:
        pass


def fetch_options(action):
    opts = []

    # get the options
    hub = connect_to_hub()
    if hub is not None:
        opts = ACTIONS[action](hub)

    # store them to cache
    with open(get_can_path(action), 'wb') as can:
        pickle.dump(opts, can)

    return opts


def main(args):
    # try cache first
    opts = load_from_cache(args.action)

    # otherwise, fetch it from the server
    if opts is None:
        opts = fetch_options(args.action)

    print(*opts)


ACTIONS = {
    'analyzers': fetch_analyzers,
    'mock-configs': fetch_mock_configs,
    'profiles': fetch_profiles
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('action', help='select what should be completed',
                        choices=ACTIONS.keys())

    main(parser.parse_args())
