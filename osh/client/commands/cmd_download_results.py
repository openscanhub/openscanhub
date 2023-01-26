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
        urllib.request.urlretrieve(url, local_path)

    def run(self, *args, **kwargs):
        username = kwargs.pop("username", None)
        password = kwargs.pop("password", None)

        if len(args) == 0:
            self.parser.error("no task ID specified")
        tasks = args

        self.dir = kwargs.pop("dir", None)

        if self.dir is not None and not os.path.isdir(self.dir):
            self.parser.error("provided directory does not exist")

        # login to the hub
        self.set_hub(username, password)

        failed = False

        for task_id in tasks:
            try:
                task_url = self.hub.client.task_url(task_id)
                try:
                    nvr = self.hub.client.task_info(task_id)['args']['srpm_name'].\
                        replace('.src.rpm', '')
                # https://gitlab.cee.redhat.com/covscan/covscan/-/issues/164
                except:  # noqa: E722
                    nvr = self.hub.client.task_info(task_id)['args']['build']['nvr']
                self.fetch_results(task_url, nvr)
            # https://gitlab.cee.redhat.com/covscan/covscan/-/issues/164
            except Exception as ex:  # noqa: B902
                failed = True
                print(ex)

        if failed:
            sys.exit(1)
