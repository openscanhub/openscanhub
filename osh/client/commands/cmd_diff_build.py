# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import os
import sys
from xmlrpc.client import Fault

from kobo.shortcuts import random_string

import osh.client
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
from osh.client.commands.shortcuts import (check_analyzers, fetch_results,
                                           handle_perm_denied, upload_file,
                                           verify_koji_build, verify_mock,
                                           verify_scan_profile_exists)
from osh.client.conf import get_conf


class Diff_Build(osh.client.OshCommand):
    """analyze a SRPM without and with patches, return diff"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        # specify command usage
        # normalized name contains a lower-case class name with underscores
        # converted to dashes
        self.parser.usage = "%%prog %s [options] <args>" % self.normalized_name
        self.parser.epilog = "User configuration file is located at: \
~/.config/osh/client.conf"

        add_config_option(self.parser)
        add_download_results_option(self.parser)
        add_comp_warnings_option(self.parser)
        add_analyzers_option(self.parser)
        add_profile_option(self.parser)
        add_csmock_args_option(self.parser)

        add_comment_option(self.parser)
        add_task_id_file_option(self.parser)
        add_nowait_option(self.parser)
        add_email_to_option(self.parser)
        add_priority_option(self.parser)
        add_nvr_option(self.parser)
        add_custom_model_option(self.parser)

        add_install_to_chroot_option(self.parser)

    def validate_results_store_file(self):
        if self.results_store_file:
            if isinstance(self.results_store_file, str):
                if not os.path.isdir(self.results_store_file):
                    self.parser.error("Path (%s) for storing results doesn't \
exist." % self.results_store_file)
            else:
                self.parser.error("Invalid path to store results.")

    def run(self, *args, **kwargs):  # noqa: C901
        local_conf = get_conf(self.conf)

        # optparser output is passed via *args (args) and **kwargs (opts)
        config = kwargs.pop("config", None)
        email_to = kwargs.pop("email_to", [])
        comment = kwargs.pop("comment")
        nowait = kwargs.pop("nowait")
        task_id_file = kwargs.pop("task_id_file")
        priority = kwargs.pop("priority")
        nvr = kwargs.pop("nvr")
        self.results_store_file = kwargs.pop("results_dir", None)
        warn_level = kwargs.pop('warn_level', '0')
        analyzers = kwargs.pop('analyzers', '')
        profile = kwargs.pop('profile', None)
        csmock_args = kwargs.pop('csmock_args', None)
        cov_custom_model = kwargs.pop('cov_custom_model', None)
        tarball_build_script = kwargs.pop('tarball_build_script', None)
        packages_to_install = kwargs.pop('install_to_chroot', None)

        if len(args) != 1:
            self.parser.error("please specify exactly one SRPM")
        if nvr:
            # self.srpm contains NVR if --nvr is used!
            self.srpm = args[0]
        else:
            self.srpm = os.path.abspath(os.path.expanduser(args[0]))

        self.validate_results_store_file()

        if nvr:
            # get build from koji
            koji_profiles = self.conf.get('KOJI_PROFILES', 'brew,koji')
            result = verify_koji_build(self.srpm, koji_profiles)
            if result is not None:
                self.parser.error(result)
        elif tarball_build_script:
            # we are analyzing tarball with build script
            if not os.path.exists(self.srpm):
                self.parser.error("Tarball does not exist.")

        if not config:
            config = local_conf.get_default_mockconfig()
            if not config:
                self.parser.error("You haven't specified mock config, there \
is not even one in your user configuration file \
(~/.config/osh/client.conf) nor in system configuration file \
(/etc/osh/client.conf)")

        # non-negative priority
        if priority is not None and priority < 0:
            self.parser.error("Priority must be a non-negative number!")

        # login to the hub
        self.connect_to_hub(kwargs)

        result = verify_mock(config, self.hub)
        if result is not None:
            self.parser.error(result)

        # options setting
        options = {
            "comment": comment,
            "mock_config": config
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

        if nvr:
            options["brew_build"] = self.srpm
            options["srpm_name"] = self.srpm
        else:
            target_dir = random_string(32)
            upload_id, err_code, err_msg = upload_file(self.hub, self.srpm,
                                                       target_dir, self.parser)
            options["upload_id"] = upload_id

        if csmock_args:
            options['csmock_args'] = csmock_args
        if cov_custom_model:
            target_dir = random_string(32)
            upload_model_id, err_code, err_msg = upload_file(self.hub,
                                                             cov_custom_model,
                                                             target_dir,
                                                             self.parser)
            options["upload_model_id"] = upload_model_id

        if packages_to_install:
            options['install_to_chroot'] = packages_to_install
        if tarball_build_script:
            options['tarball_build_script'] = tarball_build_script

        task_id = self.submit_task(config, comment, options)

        self.write_task_id_file(task_id, task_id_file)
        task_url = self.hub.client.task_url(task_id)
        print("Task info: %s" % task_url)

        if not nowait:
            from kobo.client.task_watcher import TaskWatcher
            TaskWatcher.watch_tasks(self.hub, [task_id])

            # store results if user requested this
            if self.results_store_file is not None and \
                    not fetch_results(self.hub, self.results_store_file, task_id):
                sys.exit(1)

    def submit_task(self, config, comment, options):
        try:
            return self.hub.scan.diff_build(config, comment, options)
        except Fault as e:
            handle_perm_denied(e, self.parser)
