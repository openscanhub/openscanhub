# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import os
import sys

import osh.client
from osh.client.commands.shortcuts import fetch_results


class Download_Results(osh.client.OshCommand):
    """download tarball with results of specified task"""
    enabled = True
    admin = False  # admin type account required

    def options(self):
        # specify command usage
        # normalized name contains a lower-case class name with underscores
        # converted to dashes
        self.parser.usage = f"%prog {self.normalized_name} [options] task_id [task_id...]"

        self.parser.add_option(
            "-d",
            "--dir",
            help="path to store results",
        )

    def get_nvr(self, task_args):
        """
        Obtains the NVR from the task arguments dictionary.

        * MockBuild and VersionDiffBuild tasks use either the 'srpm_name' key
          for an SRPM build or the 'build/nvr' key for Brew builds.
        * ErrataDiffBuild uses the 'build' key and used 'brew_build' key in
          the past.
        """
        if "srpm_name" in task_args:
            return task_args['srpm_name'].replace('.src.rpm', '')

        if "brew_build" in task_args:
            return task_args["brew_build"]

        nvr = task_args['build']
        if isinstance(nvr, dict):
            nvr = nvr['nvr']
        return nvr

    def run(self, *tasks, **kwargs):
        if not tasks:
            self.parser.error("no task ID specified")

        for task_id in tasks:
            if not task_id.isdigit():
                self.parser.error(f"'{task_id}' is not a number")

        results_dir = kwargs.pop("dir", None)
        if results_dir is not None and not os.path.isdir(results_dir):
            self.parser.error("provided directory does not exist")

        # login to the hub
        self.connect_to_hub(kwargs)

        failed = False

        for task_id in tasks:
            task_info = self.hub.scan.get_task_info(task_id)
            if not task_info:
                print(f"Task {task_id} does not exist!", file=sys.stderr)
                failed = True
                continue

            task_url = self.hub.client.task_url(task_id)
            nvr = self.get_nvr(task_info["args"])
            fetch_results(results_dir, task_url, nvr)

        if failed:
            sys.exit(1)
