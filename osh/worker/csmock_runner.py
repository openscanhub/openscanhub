# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import glob
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.request

from kobo.shortcuts import run

logger = logging.getLogger(__name__)


class CsmockRunner:
    """
    context manager class which executes csmock in current process
    """

    def __init__(self, tmpdir=None, create_tmpdir=False):
        if create_tmpdir:
            self.tmpdir = tempfile.mkdtemp()
            self.our_temp_dir = True
        else:
            self.tmpdir = tmpdir
            self.our_temp_dir = False

    def __enter__(self):
        self.tmpdir = tempfile.mkdtemp()
        self.our_temp_dir = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.our_temp_dir:
            try:
                shutil.rmtree(self.tmpdir)
            except OSError:
                # dangling temp dir
                # could be erased with rm -rf self.tmpdir
                pass

    def download_file(self, source_url, target_filename):
        target_path = os.path.join(self.tmpdir or os.getcwd(), target_filename)
        urllib.request.urlretrieve(source_url, target_path)
        return target_path

    def do(self, command, output_path=None, su_user=None, **kwargs):
        """ we are expecting that csmock will produce and output """
        if not command:
            logger.error("no cs* command specified!")
            raise RuntimeError("no cs* command specified!")

        if output_path:
            command += ' -o ' + output_path

        if self.tmpdir:
            if not os.path.isdir(self.tmpdir):
                logger.error('temp dir does not exists!')
                raise RuntimeError('temp dir does not exists!')
            command = f'cd {shlex.quote(self.tmpdir)} && ' + command

        if su_user:
            if self.our_temp_dir:
                inner_cmd = ['chown', f'{su_user}:{su_user}', self.tmpdir]
                try:
                    subprocess.check_call(inner_cmd)
                except subprocess.CalledProcessError:
                    subprocess.check_call(['su', '-', '-c', shlex.quote(' '.join(inner_cmd))])
                inner_cmd2 = ['chmod', 'go+rx', self.tmpdir]
                try:
                    subprocess.check_call(inner_cmd2)
                except subprocess.CalledProcessError:
                    subprocess.check_call(['su', '-', su_user, '-c', shlex.quote(' '.join(inner_cmd2))])
            command = f'su - {shlex.quote(su_user)} --session-command {shlex.quote(command)}'

        retcode, _ = run(command, stdout=True, can_fail=True, return_stdout=False, buffer_size=2, show_cmd=True, universal_newlines=True, errors="backslashreplace")
        if output_path:
            return output_path, retcode

        if self.tmpdir:
            path = self.tmpdir
        else:
            # search current directory for the results if not tmpdir is set
            path = '.'
        glob_pattern = os.path.join(path, '*.tar.xz')
        glob_results = glob.glob(glob_pattern)

        if not glob_results:
            # no .tar.xz found
            logger.info("No tarballs in '%s'", glob_pattern)
            return None, retcode

        # usually we have just one .tar.xz but, if we analyze an usptream
        # tarball which itself has .tar.xz suffix, we need to pick a file
        # ending -results.tar.xz, which appears second in the glob results
        return glob_results[-1], retcode

    def determine_output_path(self, srpm_path, result_filename):
        if result_filename is None:
            result_filename = os.path.basename(srpm_path)[:-8]
        output_path = os.path.join(self.tmpdir if self.tmpdir else os.getcwd(),
                                   result_filename + '.tar.xz')

        if output_path == srpm_path:
            # use a different output path to avoid overwriting the input tarball
            output_path = re.sub(r'\.tar\.xz$', '-results.tar.xz', output_path)
        return output_path

    def construct_cmd(self, analyzers, profile, profile_url, output_path):
        if profile == "cspodman":
            cmd = "cspodman"
        else:
            cmd = "csmock"
            if profile_url:
                profile = self.download_file(profile_url, 'mock.cfg')
                # do not cache anything when custom mock profiles are used
                cmd += ' --scrub-on-exit'
            if profile:
                cmd += ' -r ' + shlex.quote(profile)

        if analyzers:
            cmd += ' -t ' + shlex.quote(analyzers)

        if output_path:
            cmd += ' -o ' + shlex.quote(output_path)

        return cmd

    def handle_additional_arguments(self, additional_arguments):
        cmd_args = ""
        if additional_arguments:
            # split/quote/rejoin to avoid shell injection
            try:
                split_args = shlex.split(additional_arguments)

                # starting with Python 3.8, one can use + shlex.join(split_args)
                cmd_args = ' ' + ' '.join(shlex.quote(arg) for arg in split_args)
            except ValueError as e:
                logger.error("failed to parse csmock arguments: %s", e)
                raise
        return cmd_args

    def analyze(self, analyzers, srpm_path, profile=None, su_user=None, additional_arguments=None,
                result_filename=None, profile_url=None, **kwargs):

        output_path = self.determine_output_path(srpm_path, result_filename)
        cmd = self.construct_cmd(analyzers, profile, profile_url, output_path)

        try:
            cmd += self.handle_additional_arguments(additional_arguments)
        except ValueError:
            return None, 2

        cmd += ' ' + srpm_path
        return self.do(cmd, su_user=su_user, **kwargs)

    def srpm_download_analyze(self, analyzers, srpm_name, srpm_url, profile=None,
                              su_user=None, additional_arguments=None, **kwargs):
        """ download srpm from remote location and analyze it"""
        logger.debug("additional args = %s, kwargs = %s", additional_arguments, kwargs)
        srpm_path = self.download_file(srpm_url, srpm_name)
        return self.analyze(analyzers, srpm_path, profile, su_user, additional_arguments, **kwargs)

    def koji_analyze(self, analyzers, nvr, profile=None, su_user=None,
                     additional_arguments=None, koji_profile="koji", **kwargs):
        if profile == "cspodman":
            return self.analyze(analyzers, nvr, profile, su_user, additional_arguments, result_filename=nvr, **kwargs)

        download_cmd = f"koji -p {shlex.quote(koji_profile)} download-build --noprogress --arch=src {shlex.quote(nvr)}"
        try:
            workdir = self.tmpdir or os.getcwd()
            run(download_cmd, stdout=True, return_stdout=False, buffer_size=2,
                show_cmd=True, universal_newlines=True, workdir=workdir,
                errors="backslashreplace")
            srpm_path = os.path.join(workdir, nvr + '.src.rpm')
        except RuntimeError as ex:
            print(ex, file=sys.stderr)
            return None, 2

        if not os.path.exists(srpm_path):
            print("downloaded SRPM not found:", srpm_path, file=sys.stderr)
            # `brew win-build` creates build ID without .el8 but SRPM with .el8
            srpm_files = glob.glob(os.path.join(self.tmpdir, '*.src.rpm'))
            if len(srpm_files) == 1:
                srpm_path = srpm_files[0]

        if not os.path.exists(srpm_path):
            print("downloaded SRPM not found:", srpm_path, file=sys.stderr)
            return None, 2

        # check that we downloaded an RPM because koji/brew silently download
        # an HTML 404 page instead in case the build has been already deleted
        check_cmd = ['file', '--mime-type', srpm_path]
        p = subprocess.Popen(check_cmd, stdout=subprocess.PIPE)
        mime_type, _ = p.communicate()
        if not re.match(b'^.*application/x-rpm$', mime_type):
            print("unexpected MIME type:", mime_type, file=sys.stderr)
            return None, 2

        return self.analyze(analyzers, srpm_path, profile, su_user, additional_arguments, result_filename=nvr, **kwargs)

    def no_scan(self, analyzers, profile=None, su_user=None, additional_arguments=None,
                profile_url=None, **kwargs):
        """
        execute csmock command for listing analyzers and versions
        returns path to dir with results
        """
        output_path = os.path.join(self.tmpdir or os.getcwd(), 'output.tar.xz')

        if profile == "cspodman":
            cmd = "cspodman"
        else:
            cmd = "csmock"
            if profile_url:
                profile = self.download_file(profile_url, 'mock.cfg')
                # do not cache anything when custom mock profiles are used
                cmd += ' --scrub-on-exit'
            if profile:
                cmd += ' -r ' + shlex.quote(profile)

        cmd += ' -t ' + shlex.quote(analyzers)
        cmd += ' --no-scan'
        if additional_arguments:
            cmd += ' ' + additional_arguments
        return self.do(cmd, output_path=output_path, su_user=su_user, **kwargs)
