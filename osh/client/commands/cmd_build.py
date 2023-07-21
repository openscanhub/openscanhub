import os
from xmlrpc.client import Fault

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
from osh.client.commands.shortcuts import fetch_results, handle_perm_denied


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

    def prepare_task_options(self, args, kwargs):
        pass

    def run(self, *args, **kwargs):
        # login to the hub
        self.connect_to_hub(kwargs)

        # validate and parse options
        nowait = kwargs.get("nowait")
        results_dir = kwargs.get("results_dir")
        task_id_file = kwargs.get("task_id_file")
        options = self.prepare_task_options(args, kwargs)

        if results_dir is not None and not os.path.isdir(results_dir):
            self.parser.error(f"{results_dir} is not a valid directory!")

        # submit the task
        try:
            task_id = self.submit_task(options)
        except Fault as e:
            handle_perm_denied(e, self.parser)

        self.write_task_id_file(task_id, task_id_file)
        print("Task info:", self.hub.client.task_url(task_id))

        if not nowait:
            from kobo.client.task_watcher import TaskWatcher
            TaskWatcher.watch_tasks(self.hub, [task_id])

            # store results if user requested this
            if results_dir is not None:
                fetch_results(self.hub, results_dir, task_id)

    def submit_task(self, options):
        raise NotImplementedError
