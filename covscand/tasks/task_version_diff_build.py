# -*- coding: utf-8 -*-

import tempfile
import os
import pipes
import sys
import grp
import shutil
import urllib

from kobo.rpmlib import get_rpm_header
from kobo.worker import TaskBase
from kobo.shortcuts import run

import kobo.tback

from common import downloadSRPM


class VersionDiffBuild(TaskBase):
    """
        Execute diff scan between two versions/releases of a package
    """
    enabled = True

    # list of supported architectures
    arches = ["noarch"]
    # list of channels
    channels = ["default"]
    # leave False here unless you really know what you're doing
    exclusive = False
    # if True the task is not forked and runs in the worker process
    # (no matter you run worker without -f)
    foreground = False
    priority = 19
    weight = 1.0

    def run(self):
        mock_config = self.args.pop("mock_config")
        keep_covdata = self.args.pop("keep_covdata", False)
        all_checks = self.args.pop("all", False)
        security_checks = self.args.pop("security", False)
        brew_build = self.args.pop("brew_build", None)
        srpm_name = self.args.pop("srpm_name", None)
        aggressive = self.args.pop("aggressive", None)
        cppcheck = self.args.pop("cppcheck", None)
        concurrency = self.args.pop("concurrency", None)
        clang = self.args.pop('clang', None)
        no_coverity = self.args.pop('no_coverity', None)
        warning_level = self.args.pop('warning_level', None)
        path = self.args.pop('path', '')
        an_args = self.args.pop('args', [])

        # create a temp dir, make it writable by 'coverity' user
        tmp_dir = tempfile.mkdtemp(prefix="covscan_")
        os.chmod(tmp_dir, 0775)

        #change atributes of temp dir
        coverity_gid = grp.getgrnam("coverity").gr_gid
        os.chown(tmp_dir, -1, coverity_gid)

        #download srpm from brew
        if brew_build is not None:
            srpm_path = downloadSRPM(tmp_dir, brew_build)
            if not os.path.exists(srpm_path):
                print >> sys.stderr, \
                    "Invalid path %s to SRPM file (%s): %s" % \
                    (srpm_path, brew_build, kobo.tback.get_exception())
                self.fail()
        elif srpm_name is not None:
            # download SRPM
            task_url = self.hub.client.task_url(self.task_id).rstrip("/")
            srpm_path = os.path.join(tmp_dir, srpm_name)
            urllib.urlretrieve("%s/log/%s?format=raw" % (task_url,
                                                         srpm_name),
                               srpm_path)

        #is srpm allright?
        try:
            get_rpm_header(srpm_path)
        except Exception:
            print >> sys.stderr, "Invalid RPM file(%s): %s" % \
                (brew_build, kobo.tback.get_exception())
            self.fail()

        #execute mockbuild of this package
        cov_cmd = []
        cov_cmd.append("cd")
        cov_cmd.append(pipes.quote(tmp_dir))
        cov_cmd.append(";")

        # we build the command like this:
        # cd <tmp_dir> ; PATH=...:$PATH cov-*build
        if path:
            cov_cmd.append("PATH=%s:$PATH" % path)

        # $program [-fit] MOCK_PROFILE my-package.src.rpm [COV_OPTS]
        cov_cmd.append('cov-mockbuild')
        if keep_covdata:
            cov_cmd.append("-i")
        if cppcheck:
            cov_cmd.append("-c")
            if '-c' in an_args:
                an_args.remove("-c")
        if clang:
            cov_cmd.append("-l")
            if '-l' in an_args:
                an_args.remove("-l")
        if no_coverity:
            cov_cmd.append("-b")
        if warning_level:
            cov_cmd.append('-w%s' % warning_level)
        # this has to be after all analyzer-triggering args!
        if an_args:
            cov_cmd.extend(an_args)
        cov_cmd.append(pipes.quote(mock_config))
        cov_cmd.append(pipes.quote(srpm_path))
        if all_checks:
            cov_cmd.append("--all")
        if aggressive:
            cov_cmd.append("--aggressiveness-level high")
        if security_checks:
            cov_cmd.append("--security")
        if concurrency:
            cov_cmd.append("--concurrency")

        command = ["su", "-", "coverity", "-c", " ".join(cov_cmd)]

        retcode, output = run(command, can_fail=True, stdout=True,
                              buffer_size=-1, show_cmd=True)

        # upload results back to hub
        xz_path = srpm_path[:-8] + ".tar.xz"
        if not os.path.exists(xz_path):
            xz_path = srpm_path[:-8] + ".tar.lzma"
        self.hub.upload_task_log(open(xz_path, "r"),
                                 self.task_id, os.path.basename(xz_path))

        try:
            self.hub.worker.extract_tarball(self.task_id, '')
        except Exception:
            print >> sys.stderr, "Exception while extracting tarball for task \
%s: %s" % (self.task_id, kobo.tback.get_exception())
            self.fail()

        # remove temp files
        shutil.rmtree(tmp_dir)

        if retcode:
            self.fail()

        self.hub.worker.finish_task(self.task_id)

    @classmethod
    def cleanup(cls, hub, conf, task_info):
        pass
        # remove temp files, etc.

    @classmethod
    def notification(cls, hub, conf, task_info):
        hub.worker.email_task_notification(task_info["id"])
