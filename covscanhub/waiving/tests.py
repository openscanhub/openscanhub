# -*- coding: utf-8 -*-

import datetime
import os
import random

from covscanhub.other.test_enviroment import *
from covscanhub.scripts.db import set_checker_groups
from covscanhub.scan.models import *
from covscanhub.waiving.models import *
from covscanhub.waiving.service import *
from covscanhub.cs_xmlrpc.errata import create_errata_diff_scan

from unittest import TestCase
from django.test import Client
from django.conf import settings
import json
from django.db.models import Q

from kobo.hub.models import Task


class BasicWebTestCase(TestCase):
    """
    GET to all basic pages
    """

    def setUp(self):
        self.client = Client()

    def test_scans_list(self):
        r = self.client.get('/waiving/')
        self.assertEqual(r.status_code, 200)

    def test_random_scans(self):
        scan_id = random.randint(20, 100)
        r = self.client.get('/waiving/%d/' % scan_id)
        self.assertTrue(r.status_code in [200, 404])

    def test_home(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)

    def test_task_list(self):
        r = self.client.get('/task/')
        self.assertEqual(r.status_code, 200)

    def test_running_task_list(self):
        r = self.client.get('/task/running/')
        self.assertEqual(r.status_code, 200)

    def test_finished_task_list(self):
        r = self.client.get('/task/finished/')
        self.assertEqual(r.status_code, 200)

    def test_et_task_list(self):
        r = self.client.get('/task/et/')
        self.assertEqual(r.status_code, 200)

    def test_stats(self):
        r = self.client.get('/stats/')
        self.assertEqual(r.status_code, 200)

    def test_mockconfs_list(self):
        r = self.client.get('/scan/mock/')
        self.assertEqual(r.status_code, 200)


class AssetsTestCase(TestCase):
    """
    GET to all static content
    """

    def setUp(self):
        self.client = Client()

    def test_css(self):
        self.assertTrue(self.client.get('/static/css/redhat.css').status_code is not 404)
        self.assertTrue(self.client.get('/static/kobo/css/screen.css').status_code is not 404)

    def test_js(self):
        self.assertTrue(self.client.get('/static/js/jquery-1.8.3.min.js').status_code is not 404)

#class DefectsProcessingTestCase(TestCase):
#    """
#    Tests for parsing data from json file
#    """
#    @classmethod
#    def setUpClass(cls):
#        fill_db()
#        set_checker_groups()
#
#    @classmethod
#    def tearDownClass(cls):
#        clear_db()
#
#    def test_defects_loading(self):
#        f = open(os.path.join(settings.PROJECT_DIR,
#                              'other',
#                              'test_defects.js'))
#        json_data = json.load(f)
#        r = Result()
#        update_analyzer(r, json_data)
#        r.save()
#        load_defects_from_json(json_data, r, DEFECT_STATES['NEW'])
#        self.assertEqual(len(Defect.objects.all()), 2)
#        updated_result = Result.objects.all()[0]
#        self.assertEqual(updated_result.scanner, 'coverity')
#        self.assertEqual(updated_result.scanner_version, '6.5.0')
#        self.assertEqual(updated_result.lines, 123456)
#        t = datetime.datetime.strptime('00:01:45', "%H:%M:%S")
#        delta = datetime.timedelta(hours=t.hour, minutes=t.minute,
#                                   seconds=t.second)
#        self.assertEqual(updated_result.scanning_time,
#                         delta.days * 86400 + delta.seconds)
#        f.close()
#
#
#class WaivingQueriesTestCase(TestCase):
#    """
#    Tests for quries on prefilled database
#    """
#    fixtures = ['fixtures/test_fixture.json']
#
#    @classmethod
#    def setUpClass(cls):
#        fill_db()
#        set_checker_groups()
#
#    @classmethod
#    def tearDownClass(cls):
#        clear_db()
#
#    def test_verify_data(self):
#        self.assertEqual(Scan.objects.all().count(), 4)
#        active_scan = Scan.objects.get(enabled=True)
#        self.assertEqual(active_scan.parent, None)
#        first_scan = Scan.objects.get(id=2)
#        self.assertEqual(active_scan.get_child_scan(), first_scan)
#
#        failed_scan = Scan.objects.get(id=3)
#        self.assertEqual(failed_scan.get_child_scan(), None)
#        self.assertEqual(failed_scan.parent, None)
#        self.assertEqual(failed_scan.state, SCAN_STATES['FAILED'])
#
#        self.assertEqual(Result.objects.all().count(), 4)
#        self.assertEqual(Task.objects.all().count(), 4)
#
#    def test_unwaived_rgs(self):
#        sb = ScanBinding.objects.get(scan__enabled=True)
#        unw_rgs = get_unwaived_rgs(sb.result)
#        self.assertEqual(set(unw_rgs),
#                         set(ResultGroup.objects.filter(Q(id=7) | Q(id=9))))
#
#    def test_last_waiver(self):
#        cg = CheckerGroup.objects.get(id=12)
#        sb_parent = ScanBinding.objects.get(scan__id=4)
#        w = get_last_waiver(cg, sb_parent.scan.package,
#                            sb_parent.scan.tag.release)
#        self.assertEqual(w, Waiver.objects.get(id=1))
#
#    def test_results_defects_count_new(self):
#        c = Result.objects.get(id=2).get_defects_count(DEFECT_STATES['NEW'])
#        self.assertEqual(c, 3)
#        c = Result.objects.get(id=4).get_defects_count(DEFECT_STATES['NEW'])
#        self.assertEqual(c, 3)
#
#    def test_results_defects_count_fixed(self):
#        c = Result.objects.get(id=2).get_defects_count(DEFECT_STATES['FIXED'])
#        self.assertEqual(c, 1)
#        c = Result.objects.get(id=4).get_defects_count(DEFECT_STATES['FIXED'])
#        self.assertEqual(c, 2)
#
#    def test_display_in_result(self):
#        rg = ResultGroup.objects.get(id=5)
#        d = display_in_result(rg)
#        self.assertEqual(d['group_state'], 'INFO')
#        self.assertEqual(d['defects_state'], 'FIXED')
#        self.assertEqual(d['defects_count'], 1)
