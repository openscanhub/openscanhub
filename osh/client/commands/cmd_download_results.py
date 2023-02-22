import os
import sys
import urllib.request

import osh.client


class Download_Results(osh.client.CovScanCommand):
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

    def fetch_results(self, task_url, nvr):
        tarball = nvr + '.tar.xz'

        # get absolute path
        local_path = os.path.abspath(os.path.join(
            self.dir if self.dir is not None else os.curdir, tarball))

        # task_url is url to task with trailing '/'
        url = f"{task_url}log/{tarball}?format=raw"

        print(f"Downloading {tarball}", file=sys.stderr)
        urllib.request.urlretrieve(url, local_path)

    def run(self, *tasks, **kwargs):
        username = kwargs.pop("username", None)
        password = kwargs.pop("password", None)

        if not tasks:
            self.parser.error("no task ID specified")

        for task_id in tasks:
            if not task_id.isdigit():
                self.parser.error(f"'{task_id}' is not a number")

        self.dir = kwargs.pop("dir", None)

        if self.dir is not None and not os.path.isdir(self.dir):
            self.parser.error("provided directory does not exist")

        # login to the hub
        self.set_hub(username, password)

        failed = False

        for task_id in tasks:
            task_info = self.hub.scan.get_task_info(task_id)
            if not task_info:
                print(f"Task {task_id} does not exist!", file=sys.stderr)
                failed = True
                continue

            task_args = task_info["args"]
            if "srpm_name" in task_args:
                nvr = task_args['srpm_name'].replace('.src.rpm', '')
            else:
                nvr = task_args['build']
                if isinstance(nvr, dict):
                    nvr = nvr['nvr']

            task_url = self.hub.client.task_url(task_id)
            self.fetch_results(task_url, nvr)

        if failed:
            sys.exit(1)
