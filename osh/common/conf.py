import os
import sys

import kobo.conf


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
        print(f"Error: The config file '{config_file}' was not found.\n"
              f"Create the config file or specify the '{config_env}'\n"
              "environment variable to override config file location.",
              file=sys.stderr)
        return None
    return conf_dict
