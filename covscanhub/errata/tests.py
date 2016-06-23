# -*- coding: utf-8 -*-

import logging
import unittest

import koji

from covscanhub.errata.utils import get_mocks_repo
from covscanhub.errata.caps import UnifiedCapabilityChecker, FileCapabilityChecker, RPMDepCapabilityChecker
from django.conf import settings


# TODO: implement own runner and set logging level to match --verbosity
# uncomment to see more detailed output
#logger = logging.getLogger('covscanhub')
#ch = logging.StreamHandler()
#ch.setLevel(logging.DEBUG)
#logger.addHandler(ch)


class TestCap(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestCap, self).__init__(*args, **kwargs)
        self.c_dep_builds = [
            ('aspell-0.60.3-13', 'rhel-5-x86_64'),
            ('mysql55-mysql-5.5.31-9.el5', 'rhel-5-x86_64'),
            ('openldap-2.4.23-33.el6', 'rhel-6-x86_64'),
            ('wget-1.11.4-4.el6', 'rhel-6-x86_64'),
            ('hardlink-1.0-9.el6', 'rhel-6-x86_64'),
            ('coreutils-8.4-5.el6', 'rhel-6-x86_64'),
            ('libssh2-1.4.2-1.el6', 'rhel-6-x86_64'),
            ('hypervkvpd-0-0.10.el6', 'rhel-6-x86_64'),
            ('gnome-python2-desktop-2.28.0-5.el6', 'rhel-6-x86_64'),
            ('libwacom-0.5-5.el6', 'rhel-6-x86_64'),
            ('libvirt-snmp-0.0.2-4.el6', 'rhel-6-x86_64'),
            # seabios doesn't depend on libc, because it's bios
            ("seabios-0.6.1.2-28.el6", 'rhel-6-x86_64'),
            ("grub-0.97-82.el6", 'rhel-6-x86_64'),
            ('rpm-4.11.1-8.el7', 'rhel-7-x86_64'),
            # has one C source
            ('dracut-004-349.el6', 'rhel-6-x86_64'),
        ]
        self.non_c_dep_builds = [
            # fonts
            ('google-crosextra-carlito-fonts-1.103-0.1.20130920.el6.1', 'rhel-6-x86_64'),
            # SCL meta package
            ('mysql55-1-12.el5', 'rhel-5-x86_64'),
            # /etc/redhat-release
            ('redhat-release-5Server-5.10.0.2', 'rhel-5-x86_64'),
            # librtas is for ppc{,64} only, so x86_64 doesn't depend on libc.so
            ('librtas-1.3.8-1.el6', 'rhel-6-x86_64'),
            # python package
            ("system-config-lvm-1.1.12-16.el6", 'rhel-6-x86_64'),
        ]
        self.conf = {
            'dependency': 'libc.so',
            'builder': 'brew',
            'mimetypes': ['text/x-c', 'text/c-c++'],
            'extensions': ['.c', '.cpp', '.h', '.hpp'],
        }

    def test_deps(self):
        """
        This test requires package mock and profiles with names rhel-%d-x86_64.cfg
        """
        try:
            for nvr, mock in self.c_dep_builds:
                ucc = UnifiedCapabilityChecker(nvr, self.conf)
                self.assertTrue(ucc.check(mock_profile=mock, arch="x86_64"))
            for nvr, mock in self.non_c_dep_builds:
                ucc = UnifiedCapabilityChecker(nvr, self.conf)
                self.assertTrue(ucc.check(mock_profile=mock, arch="x86_64") is False)
        except AssertionError:
            import ipdb ; ipdb.set_trace()

    def test_get_mock_repo(self):
        self.assertTrue(isinstance(get_mocks_repo('rhel-6-x86_64'), (basestring, list)))

    def test_c_brew(self):
        s = koji.ClientSession(settings.BREW_URL)
        nvr = "rpm-4.11.1-8.el7"
        build = s.getBuild(nvr)
        rpms = s.listRPMs(buildID=build['id'])
        valid_rpms = filter(lambda x: x['arch'] == 'x86_64', rpms)
        rcc = RPMDepCapabilityChecker(nvr, self.conf)
        self.assertTrue(rcc.build_system(valid_rpms))

    def test_c_file(self):
        nvr = "seabios-0.6.1.2-28.el6"
        fcc = FileCapabilityChecker(nvr, self.conf)
        self.assertTrue(fcc.check())
