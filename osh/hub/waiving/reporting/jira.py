# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from django.conf import settings
from jira import JIRA

from osh.hub.waiving.models import JiraBug
from osh.hub.waiving.reporting.bug import AbstractBugReporter


class JiraReporter(AbstractBugReporter):
    def __init__(self, package, release):
        super().__init__(JiraBug, package, release)

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
