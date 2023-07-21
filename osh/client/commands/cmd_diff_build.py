# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import os

from kobo.shortcuts import random_string

from osh.client.commands.cmd_build import Base_Build
from osh.client.commands.shortcuts import (check_analyzers, upload_file,
                                           verify_koji_build, verify_mock,
                                           verify_scan_profile_exists)
from osh.client.conf import get_conf


class Diff_Build(Base_Build):
    """analyze a SRPM without and with patches, return diff"""
    enabled = True
    admin = False  # admin type account required

    def prepare_task_options(self, args, kwargs):  # noqa: C901
        local_conf = get_conf(self.conf)

        config = kwargs.pop("config", None)
        email_to = kwargs.pop("email_to", [])
        comment = kwargs.pop("comment")
        priority = kwargs.pop("priority")
        nvr = kwargs.pop("nvr")
        warn_level = kwargs.pop('warn_level', '0')
        analyzers = kwargs.pop('analyzers', '')
        profile = kwargs.pop('profile', None)
        csmock_args = kwargs.pop('csmock_args', None)
        cov_custom_model = kwargs.pop('cov_custom_model', None)
        tarball_build_script = kwargs.pop('tarball_build_script', None)
        packages_to_install = kwargs.pop('install_to_chroot', None)

        if bool(args) == bool(nvr):
            self.parser.error("please specify either SRPM or NVR")

        if args:
            if len(args) != 1:
                self.parser.error("please specify exactly one SRPM")
            self.srpm = os.path.abspath(os.path.expanduser(args[0]))

        if nvr:
            # get build from koji
            koji_profiles = self.conf.get('KOJI_PROFILES', 'brew,koji')
            result = verify_koji_build(nvr, koji_profiles)
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
            options["brew_build"] = nvr
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

        return options

    def submit_task(self, options):
        return self.hub.scan.diff_build(options['mock_config'],
                                        options['comment'],
                                        options)
