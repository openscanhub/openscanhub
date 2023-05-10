from xmlrpc.client import Fault

import bugzilla
from django.conf import settings
from django.urls import reverse

from osh.hub.other import get_or_none
from osh.hub.waiving.models import WAIVER_TYPES, Bugzilla, ResultGroup, Waiver


def has_bug(package, release):
    """
    return True if there is BZ created for specified package/release
    """
    return get_or_none(Bugzilla, package=package, release=release)


def get_unreported_bugs(package, release):
    """
    return IS_A_BUG waivers that weren't reported yet
    """
    rgs = ResultGroup.objects.select_related().filter(
        result__scanbinding__scan__package=package,
        result__scanbinding__scan__tag__release=release,
    )
    waivers = Waiver.waivers.filter(
        result_group__result__scanbinding__scan__package=package,
        result_group__result__scanbinding__scan__tag__release=release,
        state__in=[WAIVER_TYPES['IS_A_BUG'], WAIVER_TYPES['FIX_LATER']],
        bz__isnull=True,
        id__in=[rg.has_waiver().id for rg in rgs if rg.has_waiver()]
    )
    if waivers:
        return waivers.order_by('date')


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


def get_checker_groups(waivers):
    s = ""
    for n in waivers.values('result_group__checker_group__name').distinct():
        s += "%s\n" % n['result_group__checker_group__name']
    return s


def create_bug(request, package, release):
    """
    create bugzilla for package/release and fill it with all IS_A_BUG waivers
    this function should be called by view -- button "Create Bugzilla"
    """
    bz = bugzilla.Bugzilla(url=settings.BZ_URL, api_key=settings.BZ_API_KEY)
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

    data = {
        'product': release.product,
        'component': package.name,
        'summary': summary,  # 'short_desc'
        'version': release.get_prod_ver(),
        'comment': comment,
        'bug_severity': 'medium',
        'priority': 'high',
        'rep_platform': 'All',
        'op_sys': 'Linux',
        'groups': ['private'],  # others are devel, qa
    }

    if waivers[0].result_group.result.scanbinding.scan.username != \
            request.user:
        data['cc'] = [request.user.username + '@redhat.com']

    try:
        b = bz.createbug(**data)
    except Fault:
        try:
            # most likely the email in CC does not exist in BZ as user
            del data['cc']
        except KeyError:
            pass
        else:
            b = bz.createbug(**data)
    db_bz = Bugzilla()
    db_bz.release = release
    db_bz.package = package
    db_bz.number = b.bug_id
    db_bz.save()
    for w in waivers:
        w.bz = db_bz
        w.save()


def update_bug(request, package, release):
    """
    add defects to specified bugzilla that aren't there yet
    this function should be called by view -- button "update bugzilla"
    """
    bz = bugzilla.Bugzilla(url=settings.BZ_URL, api_key=settings.BZ_API_KEY)
    db_bz = has_bug(package, release)
    if db_bz:
        waivers = get_unreported_bugs(package, release)
        comment = format_waivers(waivers, request)
        bzbug = bz.getbug(db_bz.number)
        bzbug.addcomment(comment, False)
        for w in waivers:
            w.bz = db_bz
            w.save()
    else:
        create_bug(package, release)
