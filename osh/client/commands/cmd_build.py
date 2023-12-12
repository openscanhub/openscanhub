import os
import sys
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
                                        add_json_option, add_nowait_option,
                                        add_nvr_option, add_priority_option,
                                        add_profile_option,
                                        add_task_id_file_option)
from osh.client.commands.shortcuts import (check_analyzers, fetch_results,
                                           handle_perm_denied, upload_file,
                                           verify_koji_build, verify_mock,
                                           verify_scan_profile_exists)
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
        add_json_option(self.parser)
        add_nowait_option(self.parser)
        add_nvr_option(self.parser)
        add_priority_option(self.parser)
        add_profile_option(self.parser)
        add_task_id_file_option(self.parser)

    def check_build(self, args, kwargs, prefix=""):
        local_conf = get_conf(self.conf)

        config = kwargs.get(prefix + "config")
        nvr = kwargs.get(prefix + "nvr")
        srpm = kwargs.get(prefix + "srpm")
        tarball_build_script = kwargs.get("tarball_build_script")

        if not config:
            config = local_conf.get_default_mockconfig()
            if not config:
                self.parser.error("You haven't specified mock config, there \
is not even one in your user configuration file \
(~/.config/osh/client.conf) nor in system configuration file \
(/etc/osh/client.conf)")
            print(prefix + "config not specified, using default one:", config,
                  file=sys.stderr)

        result = verify_mock(config, self.hub)
        if result is not None:
            self.parser.error(result)

        options = {prefix + "mock_config": config}

        if nvr:
            # get build from koji
            koji_profiles = self.conf.get('KOJI_PROFILES', 'brew,koji')
            result = verify_koji_build(nvr, koji_profiles)
            if result is not None:
                self.parser.error(result)
            options[prefix + "brew_build"] = nvr
        else:
            if not os.path.exists(srpm):
                self.parser.error(f"file does not exist: {srpm}")

            # we are analyzing tarball with build script
            if tarball_build_script:
                options['tarball_build_script'] = tarball_build_script
            elif not srpm.endswith(".src.rpm"):
                self.parser.error(f"provided file doesn't appear to be an SRPM: {srpm}")

            target_dir = random_string(32)
            options[prefix + "upload_id"] = upload_file(self.hub, srpm,
                                                        target_dir, self.parser)

        return options

    def prepare_task_options(self, args, kwargs):
        # optparser output is passed via args (args) and kwargs (opts)
        analyzers = kwargs.get('analyzers', '')
        comment = kwargs.get("comment")
        cov_custom_model = kwargs.get('cov_custom_model')
        csmock_args = kwargs.get('csmock_args')
        email_to = kwargs.get("email_to", [])
        packages_to_install = kwargs.get('install_to_chroot')
        priority = kwargs.get("priority")
        profile = kwargs.get('profile')
        warn_level = kwargs.get('warn_level', '0')

        # non-negative priority
        if priority is not None and priority < 0:
            self.parser.error("Priority must be a non-negative number!")

        # options setting
        options = {
            "comment": comment,
            **self.check_build(args, kwargs),
        }

        if email_to:
            options["email_to"] = email_to

        if priority is not None:
            options["priority"] = priority

        if warn_level:
            options['warning_level'] = warn_level

        if analyzers:
            try:
                check_analyzers(self.hub, analyzers)
            except RuntimeError as ex:
                self.parser.error(str(ex))
            options['analyzers'] = analyzers

        if profile:
            result = verify_scan_profile_exists(self.hub, profile)
            if result is not None:
                self.parser.error(result)
            options['profile'] = profile

        if csmock_args:
            options['csmock_args'] = csmock_args

        if cov_custom_model:
            target_dir = random_string(32)
            options["upload_model_id"] = upload_file(self.hub, cov_custom_model,
                                                     target_dir, self.parser)

        if packages_to_install:
            options['install_to_chroot'] = packages_to_install

        return options

    def run(self, *args, **kwargs):
        # login to the hub
        self.connect_to_hub(kwargs)

        # validate and parse options
        nowait = kwargs.get("nowait")
        results_dir = kwargs.get("results_dir")
        task_id_file = kwargs.get("task_id_file")
        use_json = kwargs.get("json")
        options = self.prepare_task_options(args, kwargs)

        if results_dir is not None and not os.path.isdir(os.path.expanduser(results_dir)):
            self.parser.error(f"{results_dir} is not a valid directory!")

        # submit the task
        try:
            task_id = self.submit_task(options)
        except Fault as e:
            handle_perm_denied(e, self.parser)

        self.write_task_id_file(task_id, task_id_file)

        task_url = self.hub.client.task_url(task_id)
        if use_json:
            print('{"id": %d, "url": "%s"}' % (task_id, task_url))
        else:
            print("Task info:", task_url)

        if not nowait:
            from kobo.client.task_watcher import TaskWatcher
            TaskWatcher.watch_tasks(self.hub, [task_id])

            # store results if user requested this
            if results_dir is not None:
                fetch_results(self.hub, results_dir, task_id)

    def submit_task(self, options):
        raise NotImplementedError
