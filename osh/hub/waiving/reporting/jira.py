# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from django.conf import settings
from django.urls import reverse
from jira import JIRA

from osh.hub.other import get_or_none
from osh.hub.waiving.models import WAIVER_TYPES, JiraBug, ResultGroup, Waiver


class JiraReporter:
    def __init__(self, package, release):
        self.package = package
        self.release = release

    def has_bug(self):
        """
        returns True if there is a jira issue created for specified package/release
        """
        return get_or_none(JiraBug, package=self.package, release=self.release)

    def get_unreported_bugs(self):
        """
        returns IS_A_BUG waivers that weren't reported yet
        """
        rgs = ResultGroup.objects.select_related().filter(
            result__scanbinding__scan__package=self.package,
            result__scanbinding__scan__tag__release=self.release,
        )
        waivers = Waiver.waivers.filter(
            result_group__result__scanbinding__scan__package=self.package,
            result_group__result__scanbinding__scan__tag__release=self.release,
            state__in=[WAIVER_TYPES['IS_A_BUG'], WAIVER_TYPES['FIX_LATER']],
            jira_bug__isnull=True,
            id__in=[rg.has_waiver().id for rg in rgs if rg.has_waiver()]
        )
        if waivers:
            return waivers.order_by('date')

    @staticmethod
    def format_waivers(waivers, request):
        """
        returns output of waivers/defects that is posted to jira
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
        options = {
            'server': settings.JIRA_URL,
            'token_auth': settings.JIRA_API_KEY
        }
        if 'stage' in settings.JIRA_URL:
            options['proxies'] = {
                'http': 'http://squid.corp.redhat.com:3128',
                'https': 'http://squid.corp.redhat.com:3128'
            }
        return JIRA(**options)

    def create_bug(self, request):
        """
        create jira issue for package/release and fill it with all IS_A_BUG waivers
        this function should be called by view -- button "Create Jira Issue"
        """
        jira = self.__get_client()
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

        # rhel version should be in format 'rhel-X.y.0{.z}'
        version = f'rhel-{self.release.version}.0'
        if self.release.is_parent():
            version += '.z'

        data = {
            'project': {
                'key': 'RHEL',
            },
            'summary': summary,
            'components': [
                {
                    'name': self.package.name,
                },
            ],
            'versions': [
                {
                    'name': version,
                },
            ],
            # temporarily using custom field because issues.redhat.com doesn't have
            # the 'priority' field
            # see: https://gitlab.cee.redhat.com/covscan/covscan/-/issues/218
            'customfield_12316142': {  # Severity
                'id': '15655',  # Normal
            },
            'issuetype': 'Bug',
            'security': {
                'name': 'Red Hat Employee',
            },
        }

        issue_key = jira.create_issue(fields=data).key
        jira.add_comment(issue_key, comment)

        db_jira = JiraBug()
        db_jira.release = self.release
        db_jira.package = self.package
        db_jira.key = issue_key
        db_jira.save()
        for w in waivers:
            w.jira_bug = db_jira
            w.save()

    def update_bug(self, request):
        """
        add defects to specified bugzilla that aren't there yet
        this function should be called by view -- button "update bugzilla"
        """
        jira = self.__get_client()
        db_jira = self.has_bug()
        if not db_jira:
            self.create_bug(request)
            return

        waivers = self.get_unreported_bugs()

        if not waivers:
            raise ValueError("No waivers to report")

        comment = self.format_waivers(waivers, request)
        jira.add_comment(db_jira.key, comment)
        for w in waivers:
            w.jira_bug = db_jira
            w.save()
