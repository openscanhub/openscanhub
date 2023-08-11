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

        success = True
        for task_id in tasks:
            if not self.hub.scan.get_task_info(task_id):
                print(f"Task {task_id} does not exist!", file=sys.stderr)
                success = False
                continue

            success &= fetch_results(self.hub, results_dir, task_id)

        if not success:
            sys.exit(1)
