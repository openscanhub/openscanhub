# -*- coding: utf-8 -*-

from __future__ import absolute_import
from covscanhub.other.test_enviroment import *
from covscanhub.scan.models import *
from covscanhub.waiving.models import *
from .compare import *
from covscanhub.xmlrpc.errata import create_errata_diff_scan

from django.utils import unittest
from django.test import Client
from django.conf import settings

from kobo.hub.models import Task


#class ElementaryScanCreationTestCase(unittest.TestCase):
#    """
#    Tests for basic validation
#    """
#    @classmethod
#    def setUpClass(cls):
#        fill_db()
#
#    @classmethod
#    def tearDownClass(cls):
#        clear_db()
#
#    def test_prefilled_data_in_db(self):
#        """
#        Test if prefilled data in db are correct
#        """
#        self.assertEqual(len(Package.objects.all()), 3)
#        self.assertEqual(len(SystemRelease.objects.all()), 3)
#        self.assertEqual(len(MockConfig.objects.all()), 3)
#        self.assertEqual(len(Tag.objects.all()), 3)
#        u = User.objects.get(username='test_user')
#        self.assertTrue(u.has_perm('scan.errata_xmlrpc_scan'))
#        u2 = User.objects.get(username='bad_user')
#        self.assertFalse(u2.has_perm('scan.errata_xmlrpc_scan'))
#
#    def test_user_perm(self):
#        """
#        Create ordinary scan and test if this was done correctly
#        """
#        c = Client()
#        request = c.get('/xmlrpc/kerbauth/')
#        request.user = User.objects.get(username='test_user')
#        d = {}
#        response = create_errata_diff_scan(request, d)
#        self.assertEqual(response['status'], 'ERROR')
#        self.assertEqual(response['message'], 'Provided dictionary (map) \
#is empty.')
#
#        request = c.get('/xmlrpc/kerbauth/')
#        request.user = User.objects.get(username='bad_user')
#        response = create_errata_diff_scan(request, d)
#        self.assertEqual(response['status'], 'ERROR')
#        self.assertEqual(response['message'], 'You are not authorized to \
#execute this function.')
#
#    def test_scan_creation(self):
#        """
#        Create ordinary scan and test if this was done correctly
#        """
#        c = Client()
#        request = c.get('/xmlrpc/kerbauth/')
#        request.user = User.objects.get(username='test_user')
#        d = {
#            'username': 'owner',
#            'base': 'libssh2-1.2.2-7.el6',
#            'nvr': 'libssh2-1.4.2-1.el6',
#            'id': 'test_id',
#            'base_tag': 'rhel-0.1-pending',
#            'nvr_tag': 'rhel-0.1-pending',
#        }
#        response = create_errata_diff_scan(request, d)
#        self.assertEqual(response['status'], 'OK')
#
#    def test_disabled_mock(self):
#        """
#        Create scan with tag that has associated disabled mock
#        """
#        c = Client()
#        request = c.get('/xmlrpc/kerbauth/')
#        request.user = User.objects.get(username='test_user')
#        d = {
#            'username': 'owner',
#            'base': 'libssh2-1.2.2-7.el6',
#            'nvr': 'libssh2-1.4.2-1.el6',
#            'id': 'test_id',
#            'base_tag': 'rhel-1.0-release',
#            'nvr_tag': 'rhel-1.0-release',
#        }
#        response = create_errata_diff_scan(request, d)
#        self.assertEqual(response['status'], 'ERROR')
#        self.assertTrue(
#            response['message'].startswith('Unable to submit the scan, error: \
#Mock config is disabled: ')
#        )
#
#    def test_blacklisted_package(self):
#        """
#        Create scan for blacklisted package
#        """
#        c = Client()
#        request = c.get('/xmlrpc/kerbauth/')
#        request.user = User.objects.get(username='test_user')
#        d = {
#            'username': 'owner',
#            'base': 'kernel-2.6.32-220.30.1.el6',
#            'nvr': 'kernel-2.6.32-279.18.1.el6',
#            'id': 'test_id',
#            'base_tag': 'rhel-0.1-pending',
#            'nvr_tag': 'rhel-0.1-pending',
#        }
#        response = create_errata_diff_scan(request, d)
#        self.assertEqual(response['status'], 'ERROR')
#        self.assertTrue(
#            response['message'].startswith('Unable to submit the scan, error: \
#Package ') and response['message'].endswith(' is blacklisted')
#        )
#
#    def test_username(self):
#        """
#        Test if username is in provided dict
#        """
#        c = Client()
#        request = c.get('/xmlrpc/kerbauth/')
#        request.user = User.objects.get(username='test_user')
#        d = {
#            'base': 'libssh2-1.2.2-7.el6',
#            'nvr': 'libssh2-1.4.2-1.el6',
#            'id': 'test_id',
#            'base_tag': 'rhel-0.1-pending',
#            'nvr_tag': 'rhel-0.1-pending',
#        }
#        response = create_errata_diff_scan(request, d)
#        self.assertEqual(response['status'], 'ERROR')
#        self.assertTrue(
#            response['message'].startswith("Unable to submit the scan, error: \
#Key 'username' is missing from ")
#        )
#
#    def test_nvr(self):
#        """
#        Test if nvr is in provided dict
#        """
#        c = Client()
#        request = c.get('/xmlrpc/kerbauth/')
#        request.user = User.objects.get(username='test_user')
#        d = {
#            'base': 'libssh2-1.2.2-7.el6',
#            'username': 'owner',
#            'id': 'test_id',
#            'base_tag': 'rhel-0.1-pending',
#            'nvr_tag': 'rhel-0.1-pending',
#        }
#        response = create_errata_diff_scan(request, d)
#        self.assertEqual(response['status'], 'ERROR')
#        self.assertTrue(
#            response['message'].startswith("Unable to submit the scan, error: \
#Key 'nvr' is missing from ")
#        )
#
#    def test_base(self):
#        """
#        Test if base is in provided dict
#        """
#        c = Client()
#        request = c.get('/xmlrpc/kerbauth/')
#        request.user = User.objects.get(username='test_user')
#        d = {
#            'nvr': 'libssh2-1.4.2-1.el6',
#            'username': 'owner',
#            'id': 'test_id',
#            'base_tag': 'rhel-0.1-pending',
#            'nvr_tag': 'rhel-0.1-pending',
#        }
#        response = create_errata_diff_scan(request, d)
#        self.assertEqual(response['status'], 'ERROR')
#        self.assertTrue(
#            response['message'].startswith("Unable to submit the scan, error: \
#Key 'base' is missing from ")
#        )
#
#    def test_id(self):
#        """
#        Test if id is in provided dict
#        """
#        c = Client()
#        request = c.get('/xmlrpc/kerbauth/')
#        request.user = User.objects.get(username='test_user')
#        d = {
#            'nvr': 'libssh2-1.4.2-1.el6',
#            'username': 'owner',
#            'base': 'libssh2-1.2.2-7.el6',
#            'base_tag': 'rhel-0.1-pending',
#            'nvr_tag': 'rhel-0.1-pending',
#        }
#        response = create_errata_diff_scan(request, d)
#        self.assertEqual(response['status'], 'ERROR')
#        self.assertTrue(
#            response['message'].startswith("Unable to submit the scan, error: \
#Key 'id' is missing from ")
#        )
#
#    def test_nvr_tag(self):
#        """
#        Test if nvr_tag is in provided dict
#        """
#        c = Client()
#        request = c.get('/xmlrpc/kerbauth/')
#        request.user = User.objects.get(username='test_user')
#        d = {
#            'nvr': 'libssh2-1.4.2-1.el6',
#            'username': 'owner',
#            'base': 'libssh2-1.2.2-7.el6',
#            'base_tag': 'rhel-0.1-pending',
#            'id': 'test_id',
#        }
#        response = create_errata_diff_scan(request, d)
#        self.assertEqual(response['status'], 'ERROR')
#        self.assertTrue(
#            response['message'].startswith("Unable to submit the scan, error: \
#Key 'nvr_tag' is missing from ")
#        )
#
#    def test_base_tag(self):
#        """
#        Test if base_tag is in provided dict
#        """
#        c = Client()
#        request = c.get('/xmlrpc/kerbauth/')
#        request.user = User.objects.get(username='test_user')
#        d = {
#            'nvr': 'libssh2-1.4.2-1.el6',
#            'username': 'owner',
#            'base': 'libssh2-1.2.2-7.el6',
#            'nvr_tag': 'rhel-0.1-pending',
#            'id': 'test_id',
#        }
#        response = create_errata_diff_scan(request, d)
#        self.assertEqual(response['status'], 'ERROR')
#        self.assertTrue(
#            response['message'].startswith("Unable to submit the scan, error: \
#Key 'base_tag' is missing from ")
#        )
#
#
#class AdvancedScanCreationTestCase(unittest.TestCase):
#    """
#    Tests for advanced creation of scans, special cases, etc.
#    """
#    @classmethod
#    def setUpClass(cls):
#        fill_db()
#
#    @classmethod
#    def tearDownClass(cls):
#        clear_db()
#
#    def tearDown(self):
#        for scan in Scan.objects.all():
#            scan.delete()
#        for task in Task.objects.all():
#            task.delete()
#        for bind in ScanBinding.objects.all():
#            bind.delete()
#        for result in Result.objects.all():
#            result.delete()
#
#    def test_scan_inheritance(self):
#        """
#        Just a test if inheritance is working properly on valid data.
#        """
#        libssh2 = Package.objects.get(name='libssh2')
#
#        base = Scan()
#        base.scan_type = SCAN_TYPES['ERRATA_BASE']
#        base.state = SCAN_STATES['FINISHED']
#        base.nvr = 'libssh2-1.2.2-7.el6'
#        base.package = libssh2
#        base.enabled = False
#        base.username = User.objects.get(username='test_user')
#        base.tag = Tag.objects.get(name='rhel-0.1-pending')
#        base.save()
#
#        target = Scan()
#        target.scan_type = SCAN_TYPES['ERRATA']
#        target.state = SCAN_STATES['PASSED']
#        target.nvr = 'libssh2-1.2.3-1.el6'
#        target.package = libssh2
#        target.enabled = True
#        target.username = User.objects.get(username='test_user')
#        target.base = base
#        target.tag = Tag.objects.get(name='rhel-0.1-pending')
#        target.save()
#
#        base_task_id = Task.create_task(
#            owner_name='test_user',
#            label='test_task',
#            method='ErrataDiffBuild',
#            args={},
#            state=TASK_STATES["CLOSED"],
#        )
#        Task.objects.filter(id=base_task_id).update(
#            dt_finished=datetime.datetime.now())
#        target_task_id = Task.create_task(
#            owner_name='test_user',
#            label='test_task',
#            method='ErrataDiffBuild',
#            args={},
#            state=TASK_STATES["CLOSED"],
#        )
#        Task.objects.filter(id=target_task_id).update(
#            dt_finished=datetime.datetime.now())
#
#        #ACTUAL_SCANNER = ('coverity', '6.5.0')
#        base_result = Result()
#        base_result.scanner = settings.ACTUAL_SCANNER[0]
#        base_result.scanner_version = settings.ACTUAL_SCANNER[1]
#        base_result.save()
#
#        target_result = Result()
#        target_result.scanner = settings.ACTUAL_SCANNER[0]
#        target_result.scanner_version = settings.ACTUAL_SCANNER[1]
#        target_result.save()
#
#        base_bind = ScanBinding()
#        base_bind.task = Task.objects.get(id=base_task_id)
#        base_bind.scan = base
#        base_bind.result = base_result
#        base_bind.save()
#
#        target_bind = ScanBinding()
#        target_bind.task = Task.objects.get(id=target_task_id)
#        target_bind.scan = target
#        target_bind.result = target_result
#        target_bind.save()
#
#        c = Client()
#        request = c.get('/xmlrpc/kerbauth/')
#        request.user = User.objects.get(username='test_user')
#        d = {
#            'nvr': 'libssh2-1.4.2-1.el6',
#            'username': 'owner',
#            'base': 'libssh2-1.2.2-7.el6',
#            'nvr_tag': 'rhel-0.1-pending',
#            'base_tag': 'rhel-0.1-pending',
#            'id': 'test_id',
#        }
#        response = create_errata_diff_scan(request, d)
#        self.assertEqual(response['status'], 'OK')
#        self.assertEqual(len(Scan.objects.all()), 3)
#        new_scan = Scan.objects.get(nvr='libssh2-1.4.2-1.el6')
#        self.assertEqual(new_scan.base.id, base.id)
#        self.assertEqual(new_scan.get_child_scan().id, target.id)
#
#    def test_scan_inheritance_failed_scan(self):
#        """
#        There is base scan and target scan. Target scan failed and we are
#        adding new scan. We do not want the failed scan to be a child of the
#        new scan.
#        """
#        libssh2 = Package.objects.get(name='libssh2')
#
#        base = Scan()
#        base.scan_type = SCAN_TYPES['ERRATA_BASE']
#        base.state = SCAN_STATES['FINISHED']
#        base.nvr = 'libssh2-1.2.2-7.el6'
#        base.package = libssh2
#        base.enabled = False
#        base.username = User.objects.get(username='test_user')
#        base.tag = Tag.objects.get(name='rhel-0.1-pending')
#        base.save()
#
#        target = Scan()
#        target.scan_type = SCAN_TYPES['ERRATA']
#        target.state = SCAN_STATES['FAILED']
#        target.nvr = 'libssh2-1.2.3-1.el6'
#        target.package = libssh2
#        target.enabled = True
#        target.username = User.objects.get(username='test_user')
#        target.base = base
#        target.tag = Tag.objects.get(name='rhel-0.1-pending')
#        target.save()
#
#        base_task_id = Task.create_task(
#            owner_name='test_user',
#            label='test_task',
#            method='ErrataDiffBuild',
#            args={},
#            state=TASK_STATES["CLOSED"],
#        )
#        Task.objects.filter(id=base_task_id).update(
#            dt_finished=datetime.datetime.now())
#        target_task_id = Task.create_task(
#            owner_name='test_user',
#            label='test_task',
#            method='ErrataDiffBuild',
#            args={},
#            state=TASK_STATES["FAILED"],
#        )
#        Task.objects.filter(id=target_task_id).update(
#            dt_finished=datetime.datetime.now())
#
#        #ACTUAL_SCANNER = ('coverity', '6.5.0')
#        base_result = Result()
#        base_result.scanner = settings.ACTUAL_SCANNER[0]
#        base_result.scanner_version = settings.ACTUAL_SCANNER[1]
#        base_result.save()
#
#        base_bind = ScanBinding()
#        base_bind.task = Task.objects.get(id=base_task_id)
#        base_bind.scan = base
#        base_bind.result = base_result
#        base_bind.save()
#
#        target_bind = ScanBinding()
#        target_bind.task = Task.objects.get(id=target_task_id)
#        target_bind.scan = target
#        target_bind.save()
#
#        c = Client()
#        request = c.get('/xmlrpc/kerbauth/')
#        request.user = User.objects.get(username='test_user')
#        d = {
#            'nvr': 'libssh2-1.4.2-1.el6',
#            'username': 'owner',
#            'base': 'libssh2-1.2.2-7.el6',
#            'nvr_tag': 'rhel-0.1-pending',
#            'base_tag': 'rhel-0.1-pending',
#            'id': 'test_id',
#        }
#        response = create_errata_diff_scan(request, d)
#        self.assertEqual(response['status'], 'OK')
#        self.assertEqual(len(Scan.objects.all()), 3)
#        new_scan = Scan.objects.get(nvr='libssh2-1.4.2-1.el6')
#        self.assertEqual(new_scan.base.id, base.id)
#        self.assertEqual(new_scan.get_child_scan(), None)
#
#    def test_scan_inheritance_failed_parent_scan(self):
#        """
#        Case:
#            parent_scan (failed)
#              \_ child_scan (passed) <---- base_scan (passed)
#
#        We are adding new scan and we want child_scan to be a child of this
#        new scan, this:
#
#        new_scan (scanning)
#          \ parent_scan (failed)
#           \____ child_scan (passed) <---- base_scan (passed)
#        """
#        libssh2 = Package.objects.get(name='libssh2')
#
#        base = Scan()
#        base.scan_type = SCAN_TYPES['ERRATA_BASE']
#        base.state = SCAN_STATES['FINISHED']
#        base.nvr = 'libssh2-1.2.2-7.el6'
#        base.package = libssh2
#        base.enabled = False
#        base.username = User.objects.get(username='test_user')
#        base.tag = Tag.objects.get(name='rhel-0.1-pending')
#        base.save()
#
#        parent = Scan()
#        parent.scan_type = SCAN_TYPES['ERRATA']
#        parent.state = SCAN_STATES['FAILED']
#        parent.nvr = 'libssh2-1.2.4-1.el6'
#        parent.package = libssh2
#        parent.enabled = True
#        parent.username = User.objects.get(username='test_user')
#        parent.base = base
#        parent.tag = Tag.objects.get(name='rhel-0.1-pending')
#        parent.save()
#
#        target = Scan()
#        target.scan_type = SCAN_TYPES['ERRATA']
#        target.state = SCAN_STATES['PASSED']
#        target.nvr = 'libssh2-1.2.3-1.el6'
#        target.package = libssh2
#        target.enabled = True
#        target.username = User.objects.get(username='test_user')
#        target.base = base
#        target.tag = Tag.objects.get(name='rhel-0.1-pending')
#        target.parent = parent
#        target.save()
#
#        base_task_id = Task.create_task(
#            owner_name='test_user',
#            label='test_task',
#            method='ErrataDiffBuild',
#            args={},
#            state=TASK_STATES["CLOSED"],
#        )
#        Task.objects.filter(id=base_task_id).update(
#            dt_finished=datetime.datetime.now())
#        target_task_id = Task.create_task(
#            owner_name='test_user',
#            label='test_task',
#            method='ErrataDiffBuild',
#            args={},
#            state=TASK_STATES["CLOSED"],
#        )
#        Task.objects.filter(id=target_task_id).update(
#            dt_finished=datetime.datetime.now())
#        parent_task_id = Task.create_task(
#            owner_name='test_user',
#            label='test_task',
#            method='ErrataDiffBuild',
#            args={},
#            state=TASK_STATES["FAILED"],
#        )
#        Task.objects.filter(id=parent_task_id).update(
#            dt_finished=datetime.datetime.now())
#
#        #ACTUAL_SCANNER = ('coverity', '6.5.0')
#        base_result = Result()
#        base_result.scanner = settings.ACTUAL_SCANNER[0]
#        base_result.scanner_version = settings.ACTUAL_SCANNER[1]
#        base_result.save()
#
#        target_result = Result()
#        target_result.scanner = settings.ACTUAL_SCANNER[0]
#        target_result.scanner_version = settings.ACTUAL_SCANNER[1]
#        target_result.save()
#
#        base_bind = ScanBinding()
#        base_bind.task = Task.objects.get(id=base_task_id)
#        base_bind.scan = base
#        base_bind.result = base_result
#        base_bind.save()
#
#        target_bind = ScanBinding()
#        target_bind.task = Task.objects.get(id=target_task_id)
#        target_bind.scan = target
#        target_bind.result = target_result
#        target_bind.save()
#
#        c = Client()
#        request = c.get('/xmlrpc/kerbauth/')
#        request.user = User.objects.get(username='test_user')
#        d = {
#            'nvr': 'libssh2-1.4.2-1.el6',
#            'username': 'owner',
#            'base': 'libssh2-1.2.2-7.el6',
#            'nvr_tag': 'rhel-0.1-pending',
#            'base_tag': 'rhel-0.1-pending',
#            'id': 'test_id',
#        }
#        response = create_errata_diff_scan(request, d)
#        self.assertEqual(response['status'], 'OK')
#        self.assertEqual(len(Scan.objects.all()), 4)
#        new_scan = Scan.objects.get(nvr='libssh2-1.4.2-1.el6')
#        self.assertEqual(new_scan.base.id, base.id)
#        self.assertEqual(new_scan.get_child_scan().id, target.id)
#        self.assertEqual(parent.get_child_scan(), None)
#        self.assertEqual(Scan.objects.get(id=parent.id).parent, None)
#
#    def test_obsolete_scan(self):
#        """
#        There is target scan waiting in queue. Meanwhile ET submits new build,
#        so we do not want this obsolete scan to get into processing.
#        """
#        libssh2 = Package.objects.get(name='libssh2')
#
#        base = Scan()
#        base.scan_type = SCAN_TYPES['ERRATA_BASE']
#        base.state = SCAN_STATES['FINISHED']
#        base.nvr = 'libssh2-1.2.2-7.el6'
#        base.package = libssh2
#        base.enabled = False
#        base.username = User.objects.get(username='test_user')
#        base.tag = Tag.objects.get(name='rhel-0.1-pending')
#        base.save()
#
#        target = Scan()
#        target.scan_type = SCAN_TYPES['ERRATA']
#        target.state = SCAN_STATES['QUEUED']
#        target.nvr = 'libssh2-1.2.3-1.el6'
#        target.package = libssh2
#        target.enabled = True
#        target.username = User.objects.get(username='test_user')
#        target.base = base
#        target.tag = Tag.objects.get(name='rhel-0.1-pending')
#        target.save()
#
#        base_task_id = Task.create_task(
#            owner_name='test_user',
#            label='test_task',
#            method='ErrataDiffBuild',
#            args={},
#            state=TASK_STATES["CLOSED"],
#        )
#        Task.objects.filter(id=base_task_id).update(
#            dt_finished=datetime.datetime.now())
#        target_task_id = Task.create_task(
#            owner_name='test_user',
#            label='test_task',
#            method='ErrataDiffBuild',
#            args={},
#            state=TASK_STATES["FREE"],
#        )
#        Task.objects.filter(id=target_task_id).update(
#            dt_finished=datetime.datetime.now())
#
#        #ACTUAL_SCANNER = ('coverity', '6.5.0')
#        base_result = Result()
#        base_result.scanner = settings.ACTUAL_SCANNER[0]
#        base_result.scanner_version = settings.ACTUAL_SCANNER[1]
#        base_result.save()
#
#        base_bind = ScanBinding()
#        base_bind.task = Task.objects.get(id=base_task_id)
#        base_bind.scan = base
#        base_bind.result = base_result
#        base_bind.save()
#
#        target_bind = ScanBinding()
#        target_bind.task = Task.objects.get(id=target_task_id)
#        target_bind.scan = target
#        target_bind.save()
#
#        c = Client()
#        request = c.get('/xmlrpc/kerbauth/')
#        request.user = User.objects.get(username='test_user')
#        d = {
#            'nvr': 'libssh2-1.4.2-1.el6',
#            'username': 'owner',
#            'base': 'libssh2-1.2.2-7.el6',
#            'nvr_tag': 'rhel-0.1-pending',
#            'base_tag': 'rhel-0.1-pending',
#            'id': 'test_id',
#        }
#        response = create_errata_diff_scan(request, d)
#        self.assertEqual(response['status'], 'OK')
#        self.assertEqual(len(Scan.objects.all()), 3)
#        new_scan = Scan.objects.get(nvr='libssh2-1.4.2-1.el6')
#        self.assertEqual(new_scan.base.nvr, base.nvr)
#        self.assertEqual(new_scan.get_child_scan(), None)
#        self.assertEqual(new_scan.parent, None)
#        obsolete = ScanBinding.objects.get(scan__id=target.id)
#        self.assertEqual(obsolete.scan.state, SCAN_STATES['CANCELED'])
#        self.assertEqual(obsolete.task.state, TASK_STATES['CANCELED'])
#        self.assertEqual(obsolete.scan.get_child_scan(), None)
#        self.assertEqual(obsolete.scan.parent, None)


class CompareTestSuite(unittest.TestCase):
    def test1(self):
        result = get_compare_title('libssh2-1.4.2-1.el6',
                                   'libssh2-1.2.2-7.el6',)
        self.assertEqual(result, 'libssh2-1.\
<span class="result_target_nvr">4</span>.\
<span class="result_target_nvr">2</span>-\
<span class="result_target_nvr">1</span>.\
<span class="result_target_nvr">el6</span> compared to libssh2-1.\
<span class="result_base_nvr">2</span>.\
<span class="result_base_nvr">2</span>-\
<span class="result_base_nvr">7</span>.\
<span class="result_base_nvr">el6</span>')

    def test2(self):
        result = get_compare_title('wget-1.12-1.8.el6',
                                   'wget-1.12-1.4.el6',)
        self.assertEqual(result, 'wget-1.12-1.\
<span class="result_target_nvr">8</span>.\
<span class="result_target_nvr">el6</span> compared to wget-1.12-1.\
<span class="result_base_nvr">4</span>.\
<span class="result_base_nvr">el6</span>')

    def test3(self):
        result = get_compare_title('btparser-0.17-1.el6',
                                   'btparser-0.16-3.el6',)
        self.assertEqual(result, 'btparser-0.\
<span class="result_target_nvr">17</span>-\
<span class="result_target_nvr">1</span>.\
<span class="result_target_nvr">el6</span> compared to btparser-0.\
<span class="result_base_nvr">16</span>-\
<span class="result_base_nvr">3</span>.\
<span class="result_base_nvr">el6</span>')

    def test4(self):
        result = get_compare_title('sysfsutils-2.1.0-7.el6',
                                       'sysfsutils-2.1.0-6.1.el6',)
        self.assertEqual(result, 'sysfsutils-2.1.0-\
<span class="result_target_nvr">7</span>.\
<span class="result_target_nvr">el6</span> compared to sysfsutils-2.1.0-\
<span class="result_base_nvr">6</span>.\
<span class="result_base_nvr">1</span>.\
<span class="result_base_nvr">el6</span>')

    def test5(self):
        result = get_compare_title('systemd-196-1.fc19',
                                       'systemd-191-2.fc18',)
        self.assertEqual(result, 'systemd-\
<span class="result_target_nvr">196</span>-\
<span class="result_target_nvr">1</span>.\
<span class="result_target_nvr">fc19</span> compared to systemd-\
<span class="result_base_nvr">191</span>-\
<span class="result_base_nvr">2</span>.\
<span class="result_base_nvr">fc18</span>')

