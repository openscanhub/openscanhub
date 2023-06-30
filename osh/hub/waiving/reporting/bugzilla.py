# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from urllib.parse import urljoin
from xmlrpc.client import Fault

import bugzilla
from django.conf import settings
from django.urls import reverse

from osh.hub.other import get_or_none
from osh.hub.waiving.models import WAIVER_TYPES, Bugzilla, ResultGroup, Waiver


class BugzillaReporter:
    def __init__(self, package, release):
        self.package = package
        self.release = release

    def has_bug(self):
        """
        return True if there is BZ created for specified package/release
        """
        return get_or_none(Bugzilla, package=self.package, release=self.release)

    def get_unreported_bugs(self):
        """
        return IS_A_BUG waivers that weren't reported yet
        """
        rgs = ResultGroup.objects.select_related().filter(
            result__scanbinding__scan__package=self.package,
            result__scanbinding__scan__tag__release=self.release,
        )
        waivers = Waiver.waivers.filter(
            result_group__result__scanbinding__scan__package=self.package,
            result_group__result__scanbinding__scan__tag__release=self.release,
            state__in=[WAIVER_TYPES['IS_A_BUG'], WAIVER_TYPES['FIX_LATER']],
            bz__isnull=True,
            id__in=[rg.has_waiver().id for rg in rgs if rg.has_waiver()]
        )
        if waivers:
            return waivers.order_by('date')

    @staticmethod
    def format_waivers(waivers, request):
        """
        return output of waivers/defects that is posted to bugzilla
        """
        comment = ''
        for w in waivers:
            comment += "Group: %s\nDate: %s\nMessage: %s\nLink: %s\n" % (
                w.result_group.checker_group.name,
                w.date.strftime('%Y-%m-%d %H:%M:%S %Z'),  # 2013-01-04 04:09:51 EST
                w.message,
                request.build_absolute_uri(
                    reverse('waiving/waiver',
                            args=(w.result_group.result.scanbinding.id,
                                  w.result_group.id))
                )
            )
            if w != waivers.reverse()[0]:
                comment += "-" * 78 + "\n\n"
        return comment

    @staticmethod
    def get_checker_groups(waivers):
        s = ""
        for n in waivers.values('result_group__checker_group__name').distinct():
            s += "%s\n" % n['result_group__checker_group__name']
        return s

    @staticmethod
    def __get_client():
        xmlrpc_url = urljoin(settings.BZ_URL, 'xmlrpc.cgi')
        return bugzilla.Bugzilla(url=xmlrpc_url, api_key=settings.BZ_API_KEY)

    def create_bug(self, request):
        """
        create bugzilla for package/release and fill it with all IS_A_BUG waivers
        this function should be called by view -- button "Create Bugzilla"
        """
        bz = self.__get_client()
        waivers = self.get_unreported_bugs()

        if not waivers:
            raise ValueError("No waivers to report")

        scan = waivers[0].result_group.result.scanbinding.scan

        if scan.base:
            base = scan.base.nvr
        else:
            base = "NEW_PACKAGE"

        target = scan.nvr
        groups = self.get_checker_groups(waivers)

        comment = f"""
Csmock has found defect(s) in package {self.package.name}s

Package was scanned as differential scan:

    {target} <= {base}

== Reported groups of defects ==
{groups}

== Marked waivers ==
"""

        summary = 'New defect%s found in %s' % (
            's' if waivers.count() >= 2 else '',
            scan.nvr)

        comment += self.format_waivers(waivers, request)

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

        comment = self.format_waivers(waivers, request)
        bzbug = bz.getbug(db_bz.number)
        bzbug.addcomment(comment, False)
        for w in waivers:
            w.bz = db_bz
            w.save()
