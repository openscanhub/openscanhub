"""
User specific configuration
"""

import os
import sys
from configparser import SafeConfigParser

import kobo.conf

CONFIG_FILE_NAME = 'client.conf'
CONFIG_PATH_PREFIX = '.config/osh'


conf = None


class Conf:
    def __init__(self, system_conf=None):
        self.conf = self.load_config()
        self.system_conf = system_conf

    def get_conf_dir(self):
        """
        If conf dir does not exist, create it
        return full path to conf dir ( ~/.config/osh/ )
        """
        config_dir = os.path.join(os.path.expanduser('~'), CONFIG_PATH_PREFIX)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        return config_dir

    def get_config_file(self):
        """
        Returns path where configuration file lives.
        Path is <home_dir>/.config/osh/config.conf
        """
        config_path = os.path.join(self.get_conf_dir(), CONFIG_FILE_NAME)

        if not os.path.exists(config_path):
            config = SafeConfigParser()
            config.add_section('General')
            # fedora-rawhide-x86_64 is set at /etc/osh/client.conf
            # user should decide what they want in their own conf file
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
        conf = Conf(system_conf)
    return conf


def get_config_dict(config_env, config_default):
    """
    Retrieves dictionary from chosen configuration file.
    @param config_env: configuration file environment, f.e. OSH_CLIENT_CONFIG_FILE
    @param config_default: absolute file path to configuration file, usually /etc/osh/client.conf
    @return: dictionary containing configuration data
    """
    config_file = os.environ.get(config_env, config_default)
    conf_dict = kobo.conf.PyConfigParser()
    try:
        conf_dict.load_from_file(config_file)
    except (OSError, TypeError):
        print("Error: The config file '%s' was not found.\n"
              "Create the config file or specify the '%s'\n"
              "environment variable to override config file location."
              % (config_file, config_env), file=sys.stderr)
        return None
    return conf_dict
