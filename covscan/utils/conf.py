# -*- coding: utf-8 -*-
"""
User specific configuration
"""

import os

from ConfigParser import SafeConfigParser


CONFIG_FILE_NAME = 'config.conf'
CONFIG_PATH_PREFIX = '.config/covscan'


def get_home_dir():
    """
    Return user home directory
    """
    try:
        path = os.path.expanduser('~')
    except Exception:
        path = ''
    for env_var in ('HOME', 'USERPROFILE'):
        if os.path.isdir(path):
            break
        path = os.environ.get(env_var, '')
    if path:
        return path
    else:
        raise RuntimeError('Please define environment variable $HOME')


def get_conf_dir():
    """
    If conf dir does not exist, create it
    return full path to conf dir ( ~/.config/covscan/ )
    """
    config_dir = os.path.join(get_home_dir(), CONFIG_PATH_PREFIX)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    return config_dir


def get_config_file():
    """
    Returns path where configuration file lives.
    Path is <home_dir>/.config/covscan/config.conf
    """
    config_path = os.path.join(get_conf_dir(), CONFIG_FILE_NAME)

    if not os.path.exists(config_path):
        config = SafeConfigParser()
        config.add_section('General')
        config.set('General', 'DefaultMockConfig', 'fedora-rawhide-x86_64')
        f = open(config_path, 'w')
        config.write(f)
        f.close()

    return config_path


def load_config():
    """
    load configuration and return SafeConfigParser object
    """
    cf = get_config_file()
    config = SafeConfigParser()
    config.read(cf)
    return config


def get_default_mockconfig():
    """
    Return name of default MockConfig
    """
    config = load_config()
    def_config = config.get('General', 'DefaultMockConfig')
    return def_config