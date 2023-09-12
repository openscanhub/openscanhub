# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import os
from configparser import ConfigParser

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
        os.makedirs(config_dir, exist_ok=True)
        return config_dir

    def get_config_file(self):
        """
        Returns path where configuration file lives.
        Path is <home_dir>/.config/osh/config.conf
        """
        config_path = os.path.join(self.get_conf_dir(), CONFIG_FILE_NAME)

        if not os.path.exists(config_path):
            config = ConfigParser()
            config.add_section('General')
            # fedora-rawhide-x86_64 is set at /etc/osh/client.conf
            # user should decide what they want in their own conf file
            config.set('General', 'DefaultMockConfig', '')

            with open(config_path, 'w') as f:
                config.write(f)

        return config_path

    def load_config(self):
        """
        load configuration and return ConfigParser object
        """
        cf = self.get_config_file()
        config = ConfigParser()
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
