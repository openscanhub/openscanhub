# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from kobo.shortcuts import run

import os
import logging
import tempfile
import shutil

from .utils import get_mocks_repo, get_or_fail

import koji
import yum
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import six


if __name__ == '__main__':
    logger = logging.getLogger('covscanhub.errata.caps')
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)
else:
    logger = logging.getLogger(__name__)

s = koji.ClientSession(settings.BREW_URL)

class CapabilityChecker(object):
    def check(self, **kwargs):
        raise NotImplementedError()


class FileCapabilityChecker(CapabilityChecker):
    """
    This check will try to find files in package specified as NVR, (will be downloaded from build system)
    which either match provided mimetype and/or file extension
    """

    def __init__(self, nvr, conf, **kwargs):
        """
        conf = {
            'builder': 'executable used for fetching rpms',
            'mimetypes': ['text/whatever'],
            'extensions': ['.c', '.cpp'],
        }
        you have to specify either mimetypes or extensions
        """
        self.tmp_dir = tempfile.mkdtemp()
        logger.debug("tmpdir = %s", self.tmp_dir)
        os.chmod(self.tmp_dir, 0o755)
        self.builder = get_or_fail('builder', conf)
        self.mimetypes = conf.get('mimetypes', [])
        self.extensions = conf.get('extensions', [])
        if self.mimetypes == [] and self.extensions == []:
            raise RuntimeError("You have to specify either mimetypes or extensions")
        self.nvr = nvr
        self.srpm = nvr + '.src.rpm'

    def _download_srpm(self):
        cmd = [self.builder, "download-build", "--quiet", "--arch=src", self.nvr]
        try:
            run(cmd, workdir=self.tmp_dir, can_fail=False)
        except RuntimeError:
            logger.debug("Command failed: '%s'", cmd)
            logger.error("Cannot download srpm '%s' using '%s'", self.nvr, self.builder)
            raise

    def _extract_srpms(self):
        """ extract srpms by doing prep """
        # extract srpm
        cmd = "rpm2cpio %s | cpio -id" % self.srpm
        try:
            run(cmd, workdir=self.tmp_dir, can_fail=False)
        except RuntimeError:
            logger.debug("Command failed: '%s'", cmd)
            logger.error("Cannot extract srpm '%s'", self.srpm)
            raise
        # do prep
        prep_cmd = 'rpmbuild --nodeps -bp ./*spec --define="_sourcedir %(path)s" ' \
                   '--define="_topdir %(path)s" ' \
                   '--define="_builddir %(path)s"' % {"path": self.tmp_dir}
        try:
            run(prep_cmd, stdout=True, workdir=self.tmp_dir, can_fail=False)
        except RuntimeError:
            # prep failed, this could mean that the package couldn't be built
            # on this machine (exclusivearch ppc or something like that)
            logger.error("Command failed: '%s', package '%s'", prep_cmd, self.nvr)
            return False
        return True

    def find_matching_files(self):
        """ find matching files using command `file` """
        for root, dirs, files in os.walk(self.tmp_dir):
            for f in files:
                mmatch = True
                ematch = True
                fullpath = os.path.join(root, f)
                if self.mimetypes:
                    mmatch = False
                    code, mimetype = run("file -b --mime-type %s" % fullpath,
                                         can_fail=True, return_stdout=True, workdir=self.tmp_dir)
                    mimetype = mimetype.strip()
                    if mimetype in self.mimetypes:
                        logger.debug("file %s matches mimetype %s", f, mimetype)
                        mmatch = True
                if self.extensions:
                    ematch = False
                    for ext in self.extensions:
                        if fullpath.endswith(ext):
                            logger.debug("file %s matches extension %s", f, ext)
                            ematch = True
                            break
                if ematch and mmatch:
                    return True
        return False

    def check(self, **kwargs):
        try:
            self._download_srpm()
            response = self._extract_srpms()
            if response:
                response = self.find_matching_files()
        finally:
            shutil.rmtree(self.tmp_dir)
        return response


class RPMDepCapabilityChecker(CapabilityChecker):
    """
    fetch srpm, specified as nvr, from build system
    figure out what binary packages were built from it
    use yum/build system cli tool to get list of dependencies and
    figure out if one of them is valid:

      found_dependency.startswith(provided_dependency)

    (the reason for not doing exact match are sonames)
    """

    def __init__(self, nvr, conf, **kwargs):
        """
        conf = {
            'dependency': "libc.so",
        }
        """
        self.dependency = get_or_fail('dependency', conf)
        self.nvr = nvr
        self.srpm = nvr + '.src.rpm'

    def build_system(self, valid_rpms):
        """
        Check with koji if one of `valid_rpms[:]['name']` depends on `dependency`
        """
        def check_if_dep_match(item):
            try:
                dep_name = item['name']
            except KeyError:
                return False
            return dep_name.startswith(self.dependency)
        for rpm in valid_rpms:
            # get requires from brew, second arg is dependency type
            requires = s.getRPMDeps(rpm['id'], koji.DEP_REQUIRE)
            logger.debug('brew req: %s', requires)
            if any(check_if_dep_match(x) for x in requires):
                logger.info("%s depends on %s", rpm['name'], self.dependency)
                return True
        logger.info("no RPM depends on %s", self.dependency)
        return False

    def check(self, mock_profile, arch=None, **kwargs):
        """
        for q in `repoquery -s --alldeps --whatrequires libc.so*` ; do
           echo $q | rev | cut -d'-' -f3- | rev

        find out if binary packages built from `nvr` are dependant on `dependency`
        """
        # get build from koji
        build = s.getBuild(self.nvr)
        logger.debug(build)
        # list all binary packages built from srpm
        rpms = s.listRPMs(buildID=build['id'])
        logger.debug(rpms)
        # if arch is specified, use only those packages
        if arch:
            valid_rpms = [x for x in rpms if x['arch'] == arch]
            if not valid_rpms:
                logger.info("no RPMs built from '%s' for arch '%s'", self.nvr, arch)
                return False
        else:
            valid_rpms = rpms[:]

        # find out dependency using yum
        yb = yum.YumBase()
        yb.preconf.debuglevel = 0
        yb.setCacheDir()

        # get data only from mock profile's repo
        repo_url = get_mocks_repo(mock_profile)
        if repo_url:
            disabled_repos = []
            for repo in yb.repos.findRepos('*'):
                repo.disable()
                disabled_repos.append(repo)
            if isinstance(repo_url, list):
                counter = 1
                for url in repo_url:
                    yb.add_enable_repo(
                        "%s_%d" % (mock_profile, counter),
                        baseurls=[url]
                    )
                    counter += 1
            elif isinstance(repo_url, six.string_types):
                yb.add_enable_repo(mock_profile, baseurls=[repo_url])

        packages = [rpm['name'] for rpm in valid_rpms]
        try:
            pkgs = yb.pkgSack.returnNewestByNameArch(patterns=packages)
        except yum.Errors.PackageSackError as ex:
            # package was not found in repo, try brew instead
            logger.warning("depend_on, package not found in repo (%s) %s",
                           ex, packages)
            return self.build_system(valid_rpms)
        except Exception as ex:
            # there was some problem with search of package in repo using yum
            # use brew instead
            logger.warning("depend_on, yum exception %s, packages %s",
                           ex, packages)
            return self.build_system(valid_rpms)

        for pkg in pkgs:
            # alternative: for req in pkg.requires:
            logger.debug('yum package %s', pkg)
            for req in pkg.returnPrco('requires'):
                logger.debug('yum req %s', req[0])
                if req[0].startswith(self.dependency):
                    logger.info("%s depends on %s", pkg.name, self.dependency)
                    return True
        logger.info("%s do not depend on %s", packages, self.dependency)
        return False


class UnifiedCapabilityChecker(FileCapabilityChecker, RPMDepCapabilityChecker):
    """
    merge of file and rpm dep capability checker
    """
    def __init__(self, nvr, conf, **kwargs):
        FileCapabilityChecker.__init__(self, nvr, conf, **kwargs)
        RPMDepCapabilityChecker.__init__(self, nvr, conf, **kwargs)

    def check(self, **kwargs):
        has_rpm_dep = RPMDepCapabilityChecker.check(self, **kwargs)
        if not has_rpm_dep:
            return FileCapabilityChecker.check(self, **kwargs)
        return has_rpm_dep


def unified_cap_checker(**kwargs):
    """

    """
    u = UnifiedCapabilityChecker(**kwargs)
    return u.check(**kwargs)


def rpmdep_cap_checker(**kwargs):
    """

    """
    u = RPMDepCapabilityChecker(**kwargs)
    return u.check(**kwargs)


def main():
    conf = {
        'dependency': 'libc.so',
        'builder': 'brew',
        'mimetypes': ['text/x-c', 'text/c-c++'],
        'extensions': ['.c', '.cpp', '.h', '.hpp'],
        }
    import sys
    try:
        nvr = sys.argv[1]
    except IndexError:
        nvr = "system-config-lvm-1.1.12-16.el6"

    u = UnifiedCapabilityChecker(nvr, conf)
    mock = 'rhel-7-x86_64'
    print(u.check(mock_profile=mock, arch="x86_64"))


if __name__ == '__main__':
    main()
