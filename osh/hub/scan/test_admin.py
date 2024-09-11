# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.
"""Test :mod:`osh.hub.scan.admin` module."""

from django.urls import reverse
from kobo.django.auth.models import User

from osh.hub.scan.models import Scan
from osh.testing.html import parse_html
from osh.testing.testcases import OshTestCase
from osh.testing.testdata import TestDataMixin

SCANS_CHANGELIST_ITEMS_PER_PAGE = 20
SCANS_CHANGELIST_TABLE_HEADER = """
<thead>
<tr>
<th scope="col" class="action-checkbox-column">
  <div class="text">
    <span><input type="checkbox" id="action-toggle"></span>
  </div>
  <div class="clear"></div>
</th>
<th scope="col" class="sortable column-id">
  <div class="text"><a href="?o=1">ID</a></div>
  <div class="clear"></div>
</th>
<th scope="col" class="column-get_link">
  <div class="text"><span>Scan binding</span></div>
  <div class="clear"></div>
</th>
<th scope="col" class="sortable column-nvr">
  <div class="text"><a href="?o=3">NVR</a></div>
  <div class="clear"></div>
</th>
<th scope="col" class="sortable column-scan_type">
  <div class="text"><a href="?o=4">Scan type</a></div>
  <div class="clear"></div>
</th>
<th scope="col" class="sortable column-state">
  <div class="text"><a href="?o=5">State</a></div>
  <div class="clear"></div>
</th>
<th scope="col" class="column-get_link">
  <div class="text"><span>Base Scan</span></div>
  <div class="clear"></div>
</th>
<th scope="col" class="column-get_link">
  <div class="text"><span>Tag</span></div>
  <div class="clear"></div>
</th>
<th scope="col" class="column-get_link">
  <div class="text"><span>Username</span></div>
  <div class="clear"></div>
</th>
<th scope="col" class="sortable column-last_access">
  <div class="text"><a href="?o=9">Last access</a></div>
  <div class="clear"></div>
</th>
<th scope="col" class="sortable column-date_submitted">
  <div class="text"><a href="?o=10">Date submitted</a></div>
  <div class="clear"></div>
</th>
<th scope="col" class="sortable column-enabled">
  <div class="text"><a href="?o=11">Enabled</a></div>
  <div class="clear"></div>
</th>
<th scope="col" class="column-get_link">
  <div class="text"><span>Package</span></div>
  <div class="clear"></div>
</th>
<th scope="col" class="column-get_link">
  <div class="text"><span>Parent Scan</span></div>
  <div class="clear"></div>
</th>
</tr>
</thead>
"""
SCANS_CHANGELIST_TABLE_ITEM_1 = """
<tr>
  <td class="action-checkbox">
    <input type="checkbox" name="_selected_action" value="21"
           class="action-select">
  </td>
  <th class="field-id"><a href="/admin/scan/scan/21/change/">21</a></th>
  <td class="field-nvr">pkgP-1.1.1-1</td>
  <td class="field-state">INIT</td>
  <td class="field-scan_type">ERRATA</td>
  <td class="field-base_link">None</td>
  <td class="field-parent_link">None</td>
  <td class="field-tag_link">None</td>
  <td class="field-username nowrap">user1</td>
  <td class="field-package_link">
    <a href='/admin/scan/package/16/change/'>#16 pkgP</a>
  </td>
  <td class="field-scanbinding_link">None</td>
  <td class="field-enabled">
    <img src="/osh/static/admin/img/icon-yes.svg" alt="True">
  </td>
</tr>
"""
SCANS_CHANGELIST_TABLE_ITEM_2 = """
<tr>
  <td class="action-checkbox">
    <input type="checkbox" name="_selected_action" value="22"
           class="action-select">
  </td>
  <th class="field-id"><a href="/admin/scan/scan/22/change/">22</a></th>
  <td class="field-nvr">pkgA-1.2-1.el8</td>
  <td class="field-state">PASSED</td>
  <td class="field-scan_type">ERRATA</td>
  <td class="field-base_link">None</td>
  <td class="field-parent_link">None</td>
  <td class="field-tag_link">
    <a href='/admin/scan/tag/7/change/'>
      Tag: RHEL-8.6 --&gt; Mock: rhel-8-x86_64 (rhel-8.6 -- Red Hat Enterprise
      Linux 8.6)
    </a>
  </td>
  <td class="field-username nowrap">user1</td>
  <td class="field-package_link">
    <a href='/admin/scan/package/1/change/'>#1 pkgA</a>
  </td>
  <td class="field-scanbinding_link">
    <a href='/admin/scan/scanbinding/21/change/'>
      #21: Scan: #22 pkgA-1.2-1.el8 PASSED | #21 [method: DummyMethod, state:
      CLOSED, worker: Worker]
    </a>
  </td>
  <td class="field-enabled">
    <img src="/osh/static/admin/img/icon-yes.svg" alt="True">
  </td>
</tr>
"""
SCANS_CHANGELIST_TABLE_ITEM_3 = """
<tr>
  <td class="action-checkbox">
    <input type="checkbox" name="_selected_action" value="26"
           class="action-select">
  </td>
  <th class="field-id"><a href="/admin/scan/scan/26/change/">26</a></th>
  <td class="field-nvr">pkgA-1.2-5.el8</td>
  <td class="field-state">PASSED</td>
  <td class="field-scan_type">ERRATA</td>
  <td class="field-base_link">
    <a href='/admin/scan/scan/25/change/'>
      #25 pkgA-1.2-4.el8 NEEDS_INSPECTION Base: pkgA-1.2-1.el8
    </a>
  </td>
  <td class="field-parent_link">
    <a href='/admin/scan/scan/27/change/'>
      #27 pkgA-1.2-6.el8 NEEDS_INSPECTION Base: pkgA-1.2-4.el8
    </a>
  </td>
  <td class="field-tag_link">
    <a href='/admin/scan/tag/7/change/'>
      Tag: RHEL-8.6 --&gt; Mock: rhel-8-x86_64 (rhel-8.6 -- Red Hat Enterprise
      Linux 8.6)
    </a>
  </td>
  <td class="field-username nowrap">user1</td>
  <td class="field-package_link">
    <a href='/admin/scan/package/1/change/'>#1 pkgA</a>
  </td>
  <td class="field-scanbinding_link">
    <a href='/admin/scan/scanbinding/25/change/'>
      #25: Scan: #26 pkgA-1.2-5.el8 PASSED Base: pkgA-1.2-4.el8 | #25 [method:
      DummyMethod, state: CLOSED, worker: Worker]
    </a>
  </td>
  <td class="field-enabled">
    <img src="/osh/static/admin/img/icon-yes.svg" alt="True">
  </td>
</tr>
"""
SCANS_CHANGELIST_PAGINATOR = """
<p class="paginator">
  <span class="this-page">1</span>
  <a href="?p=2" class="end">2</a>
  27 scans
  <a href="?all=" class="showall">Show all</a>
</p>
"""


class ScanAdminTestSuite(OshTestCase, TestDataMixin):
    """Test suite for :class:`~osh.hub.scan.admin.ScanAdmin`."""

    @classmethod
    def setUpTestData(cls):
        # super() does not work here due to the method resolution order
        TestDataMixin.setUpTestData()
        cls.create_scans()
        cls.admin_user = User.objects.get(username="user0")
        cls.scans_total = Scan.objects.count()

    def test_changelist_is_rendered_properly(self):
        """
        Test whether change list page has all expected elements.

        The test is checking all those parts of the rendered page that are
        affected by changes in :class:`~osh.hub.scan.admin.ScanAdmin`
        and related view models. In greater detail:

        * Check every HTML element where a model name can appear.
        * Check every HTML element where a field name can appear.
        * Check the layout of the table with results.
        * Check the layout of an item of the table with results.
        * Check that links to pages where an item can be changed are working.
        * Check the number of items displayed on one page.
        * Check the paginator.

        Why this test? At now, admin view models are generated dynamically from
        corresponding database models. The purpose of this test is thus to
        catch the current state of views rendered so when a future changes or
        refactoring happens it gives a maintainer a heads up.
        """
        cls = type(self)

        self.client.force_login(cls.admin_user)
        response = self.client.get(
            reverse("admin:scan_scan_changelist"), follow=True
        )
        self.assertEqual(response.status_code, 200)

        content = response.content.decode(encoding=response.charset)
        document = parse_html(content)

        self.verify_html_title(document, "Select scan to change")
        self.verify_body_class(document, "app-scan change-list model-scan")
        # parse_html() converts HTML entities (&...;) to their Unicode
        # counterparts
        self.verify_changelist_breadcrumbs(document, "Home › Scan › Scans")
        self.verify_changelist_heading(document, "Select scan to change")
        self.verify_changelist_add_link(document, "scan")
        self.verify_changelist_select_action(
            document,
            item_plural="scans",
            items_per_page=SCANS_CHANGELIST_ITEMS_PER_PAGE,
            items_total=cls.scans_total,
        )
        self.verify_changelist_results_table(
            document,
            SCANS_CHANGELIST_TABLE_HEADER,
            SCANS_CHANGELIST_ITEMS_PER_PAGE,
            SCANS_CHANGELIST_TABLE_ITEM_1,
            SCANS_CHANGELIST_TABLE_ITEM_2,
            SCANS_CHANGELIST_TABLE_ITEM_3,
        )
        self.assertInParsedHTML(SCANS_CHANGELIST_PAGINATOR, document.body)
