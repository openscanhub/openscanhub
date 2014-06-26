# -*- coding: utf-8 -*-

import koji
import unittest

from covscanhub.errata.utils import depend_on, get_mocks_repo, depend_on_brew


class TestDepChecking(unittest.TestCase):
    def test_depend_on(self):
        """
        This test requires package mock and profiles with names rhel-%d-x86_64.cfg
        """
        self.assertTrue(depend_on('aspell-0.60.3-13', 'libc.so', 'rhel-5-x86_64'))
        self.assertTrue(depend_on('redhat-release-5Server-5.10.0.2',
                         'libc.so', 'rhel-5-x86_64') is False)
        self.assertTrue(depend_on('mysql55-mysql-5.5.31-9.el5',
                         'libc.so', 'rhel-5-x86_64'))
        self.assertTrue(depend_on('mysql55-1-12.el5', 'libc.so', 'rhel-5-x86_64') is False)
        self.assertTrue(depend_on('openldap-2.4.23-33.el6', 'libc.so', 'rhel-6-x86_64'))
        self.assertTrue(depend_on('wget-1.11.4-4.el6', 'libc.so', 'rhel-6-x86_64'))
        self.assertTrue(depend_on('hardlink-1.0-9.el6', 'libc.so', 'rhel-6-x86_64'))
        self.assertTrue(depend_on('coreutils-8.4-5.el6', 'libc.so', 'rhel-6-x86_64'))
        self.assertTrue(depend_on('libssh2-1.4.2-1.el6', 'libc.so', 'rhel-6-x86_64'))
        self.assertTrue(depend_on('hypervkvpd-0-0.10.el6', 'libc.so', 'rhel-6-x86_64'))
        self.assertTrue(depend_on('gnome-python2-desktop-2.28.0-5.el6',
                         'libc.so', 'rhel-6-x86_64'))
        self.assertTrue(depend_on('libwacom-0.5-5.el6',
                         'libc.so', 'rhel-6-x86_64'))
        # librtas is for ppc{,64} only, so x86_64 doesn't depend on libc.xo
        self.assertTrue(depend_on('librtas-1.3.8-1.el6',
                         'libc.so', 'rhel-6-x86_64') is False)
        self.assertTrue(depend_on('libvirt-snmp-0.0.2-4.el6',
                         'libc.so', 'rhel-6-x86_64'))
        self.assertTrue(depend_on("seabios-0.6.1.2-28.el6", 'libc.so', 'rhel-6-x86_64'))
        self.assertTrue(depend_on("system-config-lvm-1.1.12-16.el6", 'libc.so', 'rhel-6-x86_64'))
        self.assertTrue(depend_on("grub-0.97-82.el6", 'libc.so', 'rhel-6-x86_64'))
        self.assertTrue(depend_on('rpm-4.11.1-8.el7', 'libc.so', 'rhel-7-x86_64'))
        self.assertTrue(depend_on('google-crosextra-carlito-fonts-1.103-0.1.20130920.el6.1', 'libc.so', 'rhel-6-x86_64'))

    def test_get_mock_repo(self):
        self.assertTrue(isinstance(get_mocks_repo('rhel-6.5-x86_64'), (basestring, list)))

    def test_depend_on_brew(self):
        s = koji.ClientSession("http://brewhub.devel.redhat.com/brewhub")
        build = s.getBuild("rpm-4.11.1-8.el7")
        rpms = s.listRPMs(buildID=build['id'])
        valid_rpms = filter(lambda x: x['arch'] == 'x86_64', rpms)
        self.assertTrue(depend_on_brew(valid_rpms, 'libc.so'))
