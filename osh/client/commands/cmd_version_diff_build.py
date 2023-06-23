# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from kobo.shortcuts import random_string

from osh.client.commands.cmd_build import Base_Build
from osh.client.conf import get_conf

from .shortcuts import upload_file, verify_koji_build, verify_mock


class Version_Diff_Build(Base_Build):
    """analyze 2 SRPMs (base and target) and diff results"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        super().options()

        self.parser.add_option(
            "--base-config",
            help="specify mock config name for base package"
        )

        self.parser.add_option(
            "--base-nvr",
            help="use a Koji build for base (specified by NVR) instead of a local file"
        )

        self.parser.add_option(
            "--base-srpm",
            help="path to SRPM used as base"
        )

        self.parser.add_option(
            "--srpm",
            help="path to SRPM used as target"
        )

        # Deprecated aliases:
        self.parser.add_option("--base-brew-build", dest="base_nvr",
                               help="DEPRECATED alias for --base-nvr")

    def prepare_task_options(self, args, kwargs):
        local_conf = get_conf(self.conf)

        base_config = kwargs.get("base_config")
        base_nvr = kwargs.get("base_nvr")
        base_srpm = kwargs.get("base_srpm")
        config = kwargs.get("config")
        nvr = kwargs.get("nvr")
        srpm = kwargs.get("srpm")

        # both bases are specified
        if base_nvr and base_srpm:
            self.parser.error("Choose exactly one option (--base-nvr, --base-srpm), not both of them.")

        # both nvr/targets are specified
        if nvr and srpm:
            self.parser.error("Choose exactly one option (--nvr, --srpm), not both of them.")

        # no package option specified
        if (not base_nvr and not nvr and not srpm and not base_srpm):
            self.parser.error("Please specify both builds or SRPMs.")

        # no base specified
        if not base_nvr and not base_srpm:
            self.parser.error("You haven't specified base.")

        # no nvr/target specified
        if not nvr and not srpm:
            self.parser.error("You haven't specified target.")

        if srpm and not srpm.endswith(".src.rpm"):
            self.parser.error("provided target file doesn't appear to be \
a SRPM")

        if not base_config and config:
            kwargs["base_config"] = config
        if base_config and not config:
            kwargs["config"] = base_config

        if base_nvr:
            koji_profiles = self.conf.get('KOJI_PROFILES', 'brew,koji')
            result = verify_koji_build(base_nvr, koji_profiles)
            if result is not None:
                self.parser.error(result)

        if not base_config:
            base_config = local_conf.get_default_mockconfig()
            if not base_config:
                self.parser.error("You haven't specified mock config, there \
is not even one in your user configuration file \
(~/.config/osh/client.conf) nor in system configuration file \
(/etc/osh/client.conf)")
            print("Mock config for base not specified, using default one: %s" %
                  base_config)

        result = verify_mock(base_config, self.hub)
        if result is not None:
            self.parser.error(result)

        # prepare task options
        options = super().prepare_task_options(args, kwargs)

        options['base_mock_config'] = base_config
        if base_nvr:
            options["base_brew_build"] = base_nvr
        else:
            target_dir = random_string(32)
            upload_id, err_code, err_msg = upload_file(self.hub, base_srpm,
                                                       target_dir, self.parser)
            options["base_upload_id"] = upload_id

        return options

    def submit_task(self, options):
        return self.hub.scan.create_user_diff_task(options, {})
