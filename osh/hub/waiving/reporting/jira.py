# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from django.conf import settings
from django.urls import reverse
from jira import JIRA

from osh.hub.other import get_or_none
from osh.hub.waiving.models import WAIVER_TYPES, JiraBug, ResultGroup, Waiver


def has_bug(package, release):
    """
    returns True if there is a jira issue created for specified package/release
    """
    return get_or_none(JiraBug, package=package, release=release)


def get_unreported_bugs(package, release):
    """
    returns IS_A_BUG waivers that weren't reported yet
    """
    rgs = ResultGroup.objects.select_related().filter(
        result__scanbinding__scan__package=package,
        result__scanbinding__scan__tag__release=release,
    )
    waivers = Waiver.waivers.filter(
        result_group__result__scanbinding__scan__package=package,
        result_group__result__scanbinding__scan__tag__release=release,
        state__in=[WAIVER_TYPES['IS_A_BUG'], WAIVER_TYPES['FIX_LATER']],
        jira_bug__isnull=True,
        id__in=[rg.has_waiver().id for rg in rgs if rg.has_waiver()]
    )
    if waivers:
        return waivers.order_by('date')


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


def get_checker_groups(waivers):
    s = ""
    for n in waivers.values('result_group__checker_group__name').distinct():
        s += "%s\n" % n['result_group__checker_group__name']
    return s


def get_client():
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


def create_bug(request, package, release):
    """
    create jira issue for package/release and fill it with all IS_A_BUG waivers
    this function should be called by view -- button "Create Jira Issue"
    """
    jira = get_client()
    waivers = get_unreported_bugs(package, release)

    if waivers[0].result_group.result.scanbinding.scan.base:
        base = waivers[0].result_group.result.scanbinding.scan.base.nvr
    else:
        base = "NEW_PACKAGE"

    target = waivers[0].result_group.result.scanbinding.scan.nvr
    groups = get_checker_groups(waivers)

    comment = f"""
Csmock has found defect(s) in package {package.name}s

Package was scanned as differential scan:

    {target} <= {base}

== Reported groups of defects ==
{groups}

== Marked waivers ==
"""

    summary = 'New defect%s found in %s' % (
        's' if waivers.count() >= 2 else '',
        waivers[0].result_group.result.scanbinding.scan.nvr)

    comment += format_waivers(waivers, request)

    # rhel version should be in format 'rhel-X.y.0{.z}'
    version = f'rhel-{release.version}.0'
    if release.is_parent():
        version += '.z'

    data = {
        'project': {
            'key': 'RHEL',
        },
        'summary': summary,
        'components': [
            {
                'name': package.name,
            },
        ],
        'versions': [
            {
                'name': version,
            },
        ],
        # FIXME: temporarily using custom field because issues.redhat.com
        # doesn't have the 'priority' field
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
    db_jira.release = release
    db_jira.package = package
    db_jira.key = issue_key
    db_jira.save()
    for w in waivers:
        w.jira_bug = db_jira
        w.save()


def update_bug(request, package, release):
    """
    add defects to specified bugzilla that aren't there yet
    this function should be called by view -- button "update bugzilla"
    """
    jira = get_client()
    db_jira = has_bug(package, release)
    if not db_jira:
        create_bug(request, package, release)
        return

    waivers = get_unreported_bugs(package, release)
    comment = format_waivers(waivers, request)
    jira.add_comment(db_jira.key, comment)
    for w in waivers:
        w.jira_bug = db_jira
        w.save()
