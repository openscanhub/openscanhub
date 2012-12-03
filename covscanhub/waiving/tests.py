# -*- coding: utf-8 -*-

from covscanhub.other.test_enviroment import *
from covscanhub.scan.models import *
from covscanhub.waiving.models import *
from covscanhub.xmlrpc.errata import create_errata_diff_scan

from django.utils import unittest
from django.contrib.auth.models import User
from django.test import Client
from django.conf import settings

from kobo.hub.models import Task


class DefectsProcessingTestCase(unittest.TestCase):
    """
    Tests for advanced creation of scans, special cases, etc.
    """
    @classmethod
    def setUpClass(cls):
        fill_db()

    @classmethod
    def tearDownClass(cls):
        clear_db()

    def tearDown(self):
        for scan in Scan.objects.all():
            scan.delete()
        for task in Task.objects.all():
            task.delete()
        for bind in ScanBinding.objects.all():
            bind.delete()
        for result in Result.objects.all():
            result.delete()
    
    def test_

