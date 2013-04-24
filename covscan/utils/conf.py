# -*- coding: utf-8 -*-
"""
User specific configuration
"""

import os

from ConfigParser import SafeConfigParser


CONFIG_FILE_NAME = 'covscan.conf'
CONFIG_PATH_PREFIX = '.config/covscan'


conf = None


__all__ = (
    'get_home_dir',
    'get_conf',
)


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

            config.add_section('CIM')
            config.set('CIM', 'user', '')
            config.set('CIM', 'password', '')
            config.set('CIM', 'server', '')
            config.set('CIM', 'port', '')
            config.set('CIM', 'stream', '')

            f = open(config_path, 'w')
            config.write(f)
            f.close()

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

    def get_cim_data(self):
        """
        Return name of default MockConfig
        """
        cim_data = {
            'user': self.conf.get('CIM', 'user', False, {'user': None}),
            'passwd': self.conf.get('CIM', 'password', False, {'password': None}),
            'server': self.conf.get('CIM', 'server', False, {'server': None}),
            'port': self.conf.get('CIM', 'port', False, {'port': None}),
            'stream': self.conf.get('CIM', 'stream', False, {'stream': None}),
        }
        # when user provides only credentials and not server:port, use default
        # from system config
        if cim_data['user'] is not None and cim_data['server'] is None:
            cim_data['server'] = self.system_conf['CIM_SERVER']
            cim_data['port'] = self.system_conf['CIM_PORT']

        return cim_data


def get_conf(system_conf=None):
    global conf
    if conf is None:
        if system_conf is None:
            conf = Conf()
        else:
            conf = Conf(system_conf)
    return conf
