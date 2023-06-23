from osh.client import OshCommand
from osh.client.commands.common import (add_analyzers_option,
                                        add_comment_option,
                                        add_comp_warnings_option,
                                        add_config_option,
                                        add_csmock_args_option,
                                        add_custom_model_option,
                                        add_download_results_option,
                                        add_email_to_option,
                                        add_install_to_chroot_option,
                                        add_nowait_option, add_nvr_option,
                                        add_priority_option,
                                        add_profile_option,
                                        add_task_id_file_option)


class Base_Build(OshCommand):
    """Base class for build tasks that is not meant to be used on its own"""
    enabled = False

    def options(self):
        self.parser.usage = f"%prog {self.normalized_name} [options] <args>"
        self.parser.epilog = "User configuration file is located at: " \
                             "~/.config/osh/client.conf"

        add_analyzers_option(self.parser)
        add_comment_option(self.parser)
        add_comp_warnings_option(self.parser)
        add_config_option(self.parser)
        add_csmock_args_option(self.parser)
        add_custom_model_option(self.parser)
        add_download_results_option(self.parser)
        add_email_to_option(self.parser)
        add_install_to_chroot_option(self.parser)
        add_nowait_option(self.parser)
        add_nvr_option(self.parser)
        add_priority_option(self.parser)
        add_profile_option(self.parser)
        add_task_id_file_option(self.parser)

    def run(self, *args, **kwargs):
        pass

    def submit_task(self, options):
        raise NotImplementedError
