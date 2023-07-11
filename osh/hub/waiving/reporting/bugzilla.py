# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from urllib.parse import urljoin
from xmlrpc.client import Fault

import bugzilla
from django.conf import settings

from osh.hub.waiving.models import Bugzilla
from osh.hub.waiving.reporting.bug import AbstractBugReporter


class BugzillaReporter(AbstractBugReporter):
    def __init__(self, package, release):
        super().__init__(Bugzilla, package, release)

    @staticmethod
    def __get_client():
        xmlrpc_url = urljoin(settings.BZ_URL, 'xmlrpc.cgi')
        return bugzilla.Bugzilla(url=xmlrpc_url, api_key=settings.BZ_API_KEY)

    def __get_data(self, waivers, request):
        scan = waivers[0].result_group.result.scanbinding.scan

        summary = 'New defect%s found in %s' % (
            's' if waivers.count() >= 2 else '',
            scan.nvr)

        comment = self.get_initial_comment(waivers, request)

        data = {
            'product': self.release.product,
            'component': self.package.name,
            'summary': summary,  # 'short_desc'
            'version': self.release.version,
            'comment': comment,
            'bug_severity': 'medium',
            'priority': 'high',
            'rep_platform': 'All',
            'op_sys': 'Linux',
            'groups': ['private'],  # others are devel, qa
            'cc': [],
        }

        if scan.username != request.user:
            data['cc'].append(f'{request.user.username}@redhat.com')

        return data

    def create_bug(self, request):
        """
        create bugzilla for package/release and fill it with all IS_A_BUG waivers
        this function should be called by view -- button "Create Bugzilla"
        """
        bz = self.__get_client()
        waivers = self.get_unreported_bugs()

        if not waivers:
            raise ValueError("No waivers to report")

        data = self.__get_data(waivers, request)

        try:
            b = bz.createbug(**data)
        except Fault:
            # most likely the email in CC does not exist in BZ as user
            del data['cc']
            b = bz.createbug(**data)

        db_bz = Bugzilla()
        db_bz.release = self.release
        db_bz.package = self.package
        db_bz.number = b.bug_id
        db_bz.save()
        for w in waivers:
            w.bz = db_bz
            w.save()

    def update_bug(self, request):
        """
        add defects to specified bugzilla that aren't there yet
        this function should be called by view -- button "update bugzilla"
        """
        bz = self.__get_client()
        db_bz = self.has_bug()
        if not db_bz:
            self.create_bug(request)
            return

        waivers = self.get_unreported_bugs()

        if not waivers:
            raise ValueError("No waivers to report")

        comment = self.get_comment(waivers, request)
        bzbug = bz.getbug(db_bz.number)
        bzbug.addcomment(comment, False)
        for w in waivers:
            w.bz = db_bz
            w.save()
