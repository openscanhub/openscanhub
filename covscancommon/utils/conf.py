# -*- coding: utf-8 -*-
"""
User specific configuration
"""

from __future__ import absolute_import

import os
import sys

import kobo.conf
from six.moves.configparser import SafeConfigParser

CONFIG_FILE_NAME = 'covscan.conf'
CONFIG_PATH_PREFIX = '.config/covscan'


conf = None


__all__ = (
    'get_home_dir',
    'get_conf',
    'get_config_dict',
)


def get_home_dir():
    """
    Return user home directory
    """
    path = os.path.expanduser('~')
    if os.path.isdir(path):
        return path
    else:
        raise RuntimeError('Please define a valid environment variable $HOME')


class Conf(object):
    def __init__(self, system_conf=None):
        self.conf = self.load_config()
        self.system_conf = system_conf

    def get_conf_dir(self):
        """
        If conf dir does not exist, create it
        return full path to conf dir ( ~/.config/covscan/ )
        """
        config_dir = os.path.join(get_home_dir(), CONFIG_PATH_PREFIX)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        return config_dir

    def get_config_file(self):
        """
        Returns path where configuration file lives.
        Path is <home_dir>/.config/covscan/config.conf
        """
        config_path = os.path.join(self.get_conf_dir(), CONFIG_FILE_NAME)

        if not os.path.exists(config_path):
            config = SafeConfigParser()
            config.add_section('General')
            # fedora-rawhide-x86_64 is set at /etc/covscan/covscan.conf
            # user should decide what does he want at his own conf file
            config.set('General', 'DefaultMockConfig', '')

            with open(config_path, 'w') as f:
                config.write(f)

        return config_path

    def load_config(self):
        """
        load configuration and return SafeConfigParser object
        """
        cf = self.get_config_file()
        config = SafeConfigParser()
        config.read(cf)
        return config

    def get_default_mockconfig(self):
        """
        Return name of default MockConfig
        """
        def_config = self.conf.get('General', 'DefaultMockConfig')
        if not def_config:
            def_config = self.system_conf['DEFAULT_MOCKCONFIG']
        return def_config


def get_conf(system_conf=None):
    global conf
    if conf is None:
        if system_conf is None:
            conf = Conf()
        else:
            conf = Conf(system_conf)
    return conf


def get_config_dict(config_env, config_default):
    """
    Retrieves dictionary from chosen configuration file.
    @param config_env: configuration file environment, f.e. COVSCAN_CONFIG_FILE
    @param config_default: absolute file path to configuration file, usually /etc/covscan/covscan.conf
    @return: dictionary containing configuration data
    """
    config_file = os.environ.get(config_env, config_default)
    conf_dict = kobo.conf.PyConfigParser()
    try:
        conf_dict.load_from_file(config_file)
    except (IOError, TypeError):
        sys.stderr.write("\n\nError: The config file '%s' was not found.\n"
                         "Create the config file or specify the '%s'\n"
                         "environment variable to override config file location.\n"
                         % (config_default, config_env))
        return None
    return conf_dict
