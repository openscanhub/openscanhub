import os
from xmlrpc.client import Fault

from kobo.shortcuts import random_string

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
from osh.client.commands.shortcuts import (fetch_results, handle_perm_denied,
                                           upload_file, verify_koji_build,
                                           verify_mock)
from osh.client.conf import get_conf


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

    def check_build(self, args, kwargs):
        local_conf = get_conf(self.conf)

        config = kwargs.get("config")
        nvr = kwargs.get("nvr")
        srpm = kwargs.get("srpm")
        tarball_build_script = kwargs.get("tarball_build_script")

        if not config:
            config = local_conf.get_default_mockconfig()
            if not config:
                self.parser.error("You haven't specified mock config, there \
is not even one in your user configuration file \
(~/.config/osh/client.conf) nor in system configuration file \
(/etc/osh/client.conf)")
            print("config not specified, using default one:", config)

        result = verify_mock(config, self.hub)
        if result is not None:
            self.parser.error(result)

        options = {"mock_config": config}

        if nvr:
            # get build from koji
            koji_profiles = self.conf.get('KOJI_PROFILES', 'brew,koji')
            result = verify_koji_build(nvr, koji_profiles)
            if result is not None:
                self.parser.error(result)
            options["brew_build"] = nvr
        else:
            # we are analyzing tarball with build script
            if tarball_build_script:
                if not os.path.exists(srpm):
                    self.parser.error("Tarball does not exist.")
                options['tarball_build_script'] = tarball_build_script

            target_dir = random_string(32)
            upload_id, *_ = upload_file(self.hub, srpm, target_dir, self.parser)
            options["upload_id"] = upload_id

        return options

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
