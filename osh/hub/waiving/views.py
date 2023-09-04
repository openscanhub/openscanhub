# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import datetime
import logging
import os
from urllib.parse import urlencode

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic.list import ListView

from osh.common.constants import (ERROR_DIFF_FILE, ERROR_HTML_FILE,
                                  ERROR_TXT_FILE, FIXED_DIFF_FILE,
                                  FIXED_HTML_FILE, FIXED_TXT_FILE)
from osh.hub.other import get_or_none
from osh.hub.scan.compare import get_compare_title
from osh.hub.scan.models import (SCAN_STATES, SCAN_TYPES_TARGET, ETMapping,
                                 Package, Scan, ScanBinding, SystemRelease)
from osh.hub.scan.notify import send_notif_new_comment
from osh.hub.scan.service import get_latest_sb_by_package
from osh.hub.scan.xmlrpc_helper import scan_notification_email
from osh.hub.service.processing import task_has_results
from osh.hub.waiving.forms import ScanListSearchForm, WaiverForm
from osh.hub.waiving.models import (DEFECT_STATES, RESULT_GROUP_STATES,
                                    WAIVER_LOG_ACTIONS, WAIVER_TYPES,
                                    WAIVER_TYPES_HELP_TEXTS, Bugzilla,
                                    CheckerGroup, Defect, JiraBug, ResultGroup,
                                    Waiver, WaivingLog)
from osh.hub.waiving.reporting import bugzilla, jira
from osh.hub.waiving.service import (apply_waiver, display_in_result,
                                     get_last_waiver, get_unwaived_rgs,
                                     get_waivers_for_rg, waiver_condition)

logger = logging.getLogger(__name__)


def get_common_context(request, sb):
    """
    Return common context data
    """
    context = add_logs_to_context(sb)
    # title
    if sb.scan.base:
        context['compare_title'] = get_compare_title(
            sb.scan.nvr,
            sb.scan.base.nvr,
        )
        context['title'] = "%s compared to %s" % (
            sb.scan.nvr,
            sb.scan.base.nvr,
        )
    else:
        context['compare_title'] = sb.scan.nvr
        context['title'] = sb.scan.nvr
    # link to ET
    mappings = sb.etmapping_set.all()
    if mappings:
        advisory_id = sb.etmapping_set.all()[0].advisory_id
        context['advisory_link'] = "%s/advisory/%s/test_run/covscan" % (
            settings.ET_URL, advisory_id)
    if 'status_message' in request.session:
        context['status_message'] = request.session.pop('status_message')

    return context


def get_result_context(request, sb):
    """
    Get all the common data for waiver
    """
    context = get_common_context(request, sb)
    package = sb.scan.package
    release = sb.scan.tag.release if sb.scan.tag else None

    context['bz_url'] = settings.BZ_URL
    context['jira_url'] = settings.JIRA_URL

    unrep_bz_waivers = bugzilla.get_unreported_bugs(package, release)
    unrep_jira_waivers = jira.get_unreported_bugs(package, release)

    context['bugzilla'] = get_or_none(Bugzilla,
                                      package=package,
                                      release=release)

    context['jira'] = get_or_none(JiraBug,
                                  package=package,
                                  release=release)

    if unrep_bz_waivers:
        context['unreported_bugs_count_bz'] = unrep_bz_waivers.count()
    else:
        context['unreported_bugs_count_bz'] = 0

    if unrep_jira_waivers:
        context['unreported_bugs_count_jira'] = unrep_jira_waivers.count()
    else:
        context['unreported_bugs_count_jira'] = 0

    # numbers
    if sb.result:
        n_out, n_count = get_waiving_data(sb.result,
                                          defect_type=DEFECT_STATES['NEW'])
        new_defects = get_tupled_data(n_out)

        f_out, f_count = get_waiving_data(sb.result,
                                          defect_type=DEFECT_STATES['FIXED'])
        fixed_defects = get_tupled_data(f_out)

        o_out, o_count = get_waiving_data(
            sb.result,
            defect_type=DEFECT_STATES['PREVIOUSLY_WAIVED'])
        old_defects = get_tupled_data(o_out)
        context['output_new'] = new_defects
        context['output_fixed'] = fixed_defects
        context['output_old'] = old_defects

        # number of active groups in each tab
        context['new_count'] = n_count
        context['fixed_count'] = f_count
        context['old_count'] = o_count
    elif sb.scan.state == SCAN_STATES['FAILED']:
        context['not_finished'] = "Scan wasn't successfull. \
We are checking what happened."
    elif sb.scan.state == SCAN_STATES['CANCELED']:
        context['not_finished'] = "Scan is canceled (is superseded by newer \
one)."
    else:
        context['not_finished'] = "Scan not complete."
    context['sb'] = sb
    # links for other runs
    context['first_sb'] = sb.scan.get_first_scan_binding()
    context['newest_sb'] = \
        get_latest_sb_by_package(release, sb.scan.package)
    context['previous_sb'] = getattr(sb.scan.get_child_scan(),
                                     'scanbinding', None)
    context['next_sb'] = getattr(sb.scan.parent, 'scanbinding', None)
    ids = list(sb.scan.all_scans_in_release().values_list('id', flat=True))
    if sb.scan.id not in ids:
        context['scan_order'] = '#'
    else:
        context['scan_order'] = ids.index(sb.scan.id) + 1
    context['scans_count'] = sb.scan.all_scans_in_release().count()

    return context


def create_log_dict(title, icon, icon_link, files, logs_list):
    """
    create log -- dict; files is a list of tuples:
        [(path, title, ), ]
    """
    f = []
    for t in files:
        if t[0] in logs_list:
            f.append({'path': t[0], 'title': t[1]})
    if not f:
        return {}
    log = {
        'title': title,
        'icon': icon,
        'icon_link': icon_link,
        'files': f,
    }
    return log


def add_logs_to_context(sb):
    logs = []
    logs_list = sb.task.logs.list

    if task_has_results(sb.task):
        log_prefix = os.path.join(sb.scan.nvr, 'scan-results')
    else:
        log_prefix = os.path.join(sb.scan.nvr, 'run1', 'results')

    logs.append(create_log_dict('Important defects', 'Document_content_32.png',
                                log_prefix + '-imp.html',
                                [(log_prefix + '-imp.err', 'TXT'),
                                 (log_prefix + '-imp.html', 'HTML'),
                                 (log_prefix + '-imp.js', 'JSON')], logs_list))
    logs.append(create_log_dict('Added defects', 'Warning_32.png',
                                ERROR_HTML_FILE,
                                [(ERROR_TXT_FILE, 'TXT'),
                                 (ERROR_HTML_FILE, 'HTML'),
                                 (ERROR_DIFF_FILE, 'JSON')], logs_list))
    logs.append(create_log_dict('Fixed defects', 'Ok_32.png',
                                FIXED_HTML_FILE,
                                [(FIXED_TXT_FILE, 'TXT'),
                                 (FIXED_HTML_FILE, 'HTML'),
                                 (FIXED_DIFF_FILE, 'JSON')], logs_list))
    logs.append(create_log_dict('All defects', 'Document_content_32.png',
                                log_prefix + '.html',
                                [(log_prefix + '.err', 'TXT'),
                                 (log_prefix + '.html', 'HTML'),
                                 (log_prefix + '.js', 'JSON')], logs_list))
    logs.append(create_log_dict('Scan Log', 'Message_log_32.png',
                                'stdout.log',
                                [('stdout.log', 'TXT')], logs_list))

    return {'logs': [x for x in logs if x]}


def get_waiving_data(result_object, defect_type):
    """return list of checker_groups with states and counts"""
    output = {}
    count = 0
    # checker_group: result_group
    for group in CheckerGroup.objects.filter(enabled=True):
        try:
            rg = ResultGroup.objects.get(checker_group=group,
                                         result=result_object,
                                         defect_type=defect_type)
        except ObjectDoesNotExist:
            output[group] = {}
        else:
            count += 1
            view_data = display_in_result(rg)
            view_data['id'] = rg.id
            output[group] = view_data
    return output, count


def get_tupled_data(output):
    result_tuples = []
    i = 0

    # find best match: 6 is too much and 3 is too few
    # FIXME: 5 columns doesn't work
    # if len(output.keys()) % 4 == 0:
    column_count = 4
    # else:
    #    column_count = 5

    output_keys = list(output.keys())
    while True:
        low_bound = column_count * i
        high_bound = column_count * (i + 1)
        if low_bound + 1 > len(output_keys):
            break
        tmp = {}
        for k in output_keys[low_bound:high_bound]:
            tmp[k] = output[k]
        result_tuples.append(tmp)
        i += 1
    return result_tuples


class ResultsListView(ListView):
    """
    Display list of runs; request['GET'] may contain order_by
    """
    allow_empty = True
    paginate_by = 50
    template_name = "waiving/list.html"
    context_object_name = "scanbinding_list"
    title = "List of scan results"

    def order_scans(self):
        order_by = self.request.GET.get('order_by', None)
        order_prefix = ''
        # mapping between ?order_by=name and .order_by(...) -- nicer URLs
        order_by_mapping = {
            'id': 'id',
            'target': 'scan__nvr',
            'base': 'scan__base__nvr',
            'state': 'scan__state',
            'access': 'scan__last_access',
            'user': 'scan__username',
            'release': 'scan__tag__release__tag',
        }

        # custom sort or default one?
        if order_by:
            # will it be asc or desc sort?
            if order_by.startswith('-'):
                order_prefix = '-'
                order_by = order_by[1:]

            if order_by not in order_by_mapping:
                raise Http404('Unknown column to order by: ' + order_by)

            order = order_prefix + order_by_mapping[order_by]
        else:
            # order by scan__date, because result might not exist
            order = '-scan__date_submitted'

        def generate_url(args, order_key):
            """args = request.GET, order_key = "name" | "-user" """
            args['order_by'] = order_key
            url = urlencode(args)
            if url:
                return '?' + url
            else:
                return ""

        # link sort URLs to template
        self.table_sort = {}
        for o in order_by_mapping:
            t = self.request.GET.copy()

            # generate URL + CSS style for clicked sorter
            if order_by == o:
                if not order_prefix:
                    self.table_sort[o] = generate_url(t, '-' + o), 'down'
                else:
                    self.table_sort[o] = generate_url(t, o), 'up'
            else:
                self.table_sort[o] = generate_url(t, o), 'undef'
        return order

    def get_queryset(self):
        self.search_form = ScanListSearchForm(self.request.GET)
        q = ScanBinding.objects.filter(
            scan__scan_type__in=SCAN_TYPES_TARGET)
        if self.search_form.is_valid():
            q = q.filter(self.search_form.get_query(self.request))
            q = self.search_form.objects_satisfy(q)
        return q.order_by(self.order_scans()).select_related()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = self.search_form
        context['table_sort'] = self.table_sort
        context['title'] = self.title

        # to make pagination work with filtering
        args = self.request.GET.copy()
        try:
            del args['page']
        except KeyError:
            pass
        if args:
            context['get_vars'] = '&' + urlencode(args)

        return context


def comment_post(request, form, sb, result_group_object, url_name_next,
                 active_tab, defects_list_class):
    """ Add comment to RG """
    wl = WaivingLog()
    wl.user = request.user
    wl.state = WAIVER_LOG_ACTIONS['NEW']

    w = Waiver()
    w.message = form.cleaned_data['message']
    w.result_group = result_group_object
    w.user = request.user
    w.is_active = False
    w.state = WAIVER_TYPES[form.cleaned_data['waiver_type']]
    w.save()

    wl.waiver = w
    wl.save()

    s = sb.scan
    s.last_access = datetime.datetime.now()
    s.save()

    if s.username != wl.user:
        send_notif_new_comment(request, s, wl)

    logger.info('Comment %s submitted for resultgroup %s',
                w, result_group_object)
    request.session['status_message'] = \
        "Comment (%s) successfully submitted." % (
        w.message[:50].rstrip() + '... ' if len(w.message) > 50
        else w.message)

    request.session['active_tab'] = active_tab
    request.session['defects_list_class'] = defects_list_class

    prim_url = reverse("waiving/result", args=(sb.id, ))

    rgs = get_unwaived_rgs(result_group_object.result)
    if 'submit_next' in request.POST:
        if rgs:
            return HttpResponseRedirect(reverse(url_name_next,
                                                args=(sb.id, rgs[0].id)))
    return HttpResponseRedirect(prim_url)


def waiver_post(form, request, sb, result_group_object, url_name,
                url_name_next, active_tab, defects_list_class):
    """adding new waiver/marking group as TP"""
    if 'COMMENT' == form.cleaned_data['waiver_type']:
        return comment_post(request, form, sb, result_group_object,
                            url_name_next, active_tab, defects_list_class)
    wl = WaivingLog()
    wl.user = request.user
    if result_group_object.has_waiver():
        wl.state = WAIVER_LOG_ACTIONS['REWAIVE']
    else:
        wl.state = WAIVER_LOG_ACTIONS['NEW']

    lws = Waiver.objects.filter(result_group=result_group_object)
    if lws:
        lw = lws.latest()
        lw.is_active = False
        lw.save()

    w = Waiver()
    w.message = form.cleaned_data['message']
    w.result_group = result_group_object
    w.user = request.user
    w.is_active = True
    w.state = WAIVER_TYPES[form.cleaned_data['waiver_type']]
    w.save()

    wl.waiver = w
    wl.save()

    s = sb.scan

    if result_group_object.is_previously_waived():
        result_group_object.defect_type = DEFECT_STATES['NEW']
        Defect.objects.filter(result_group=result_group_object).\
            update(state=DEFECT_STATES['NEW'])
        result_group_object.save()

    # update states of sb and rg; eventually of whole run
    apply_waiver(result_group_object, sb, w)

    s.last_access = datetime.datetime.now()
    s.save()

    logger.info('Waiver %s submitted for resultgroup %s',
                w, result_group_object)
    request.session['status_message'] = \
        "Waiver (%s) successfully submitted." % (
        w.message[:50].rstrip() + '... ' if len(w.message) > 50
        else w.message)

    request.session['active_tab'] = active_tab
    request.session['defects_list_class'] = defects_list_class

    rgs = get_unwaived_rgs(result_group_object.result)
    if not rgs:
        request.session['status_message'] += " Everything is waived."
    if 'submit_next' in request.POST:
        if rgs:
            return HttpResponseRedirect(reverse(url_name_next,
                                                args=(sb.id, rgs[0].id)))
    prim_url = reverse("waiving/result", args=(sb.id, ))
    return HttpResponseRedirect(prim_url)


def waiver(request, sb_id, result_group_id):
    """
    Display waiver (for new defects) for specified result & group
    """
    context = {}

    sb = get_object_or_404(ScanBinding, id=sb_id)
    result_group_object = get_object_or_404(ResultGroup, id=result_group_id)

    # this could help user to determine if this is FP or not
    previous_waivers = result_group_object.previous_waivers()
    if previous_waivers:
        context['previous_waivers'] = previous_waivers

    if request.method == "POST":
        form = WaiverForm(request.POST)

        if form.is_valid():
            return waiver_post(form, request, sb, result_group_object,
                               'waiving/waiver', 'waiving/waiver',
                               "new_selected", "new")
        else:
            context['status_message'] = 'Invalid submission. For more ' \
                'details, see form.'
    else:
        if previous_waivers:
            form = WaiverForm(initial={'message': previous_waivers[0].message})
        else:
            form = WaiverForm()

    context['display_waivers'] = True
    if sb.scan.enabled:
        context['form'] = form
        context['display_form'] = True
        context['waiver_type_helpers'] = \
            [(WAIVER_TYPES.get_item_help_text(k), v) for k, v in
                WAIVER_TYPES_HELP_TEXTS.items()]
    else:
        context['display_form'] = False
        context['form_message'] = 'This is not the newest scan.'

    # merge already created context with result context
    context = context.copy()  # TODO: check if .copy() is really needed
    context.update(get_result_context(request, sb))

    context['active_group'] = result_group_object
    context['defects'] = Defect.objects.filter(result_group=result_group_id,
                                               state=DEFECT_STATES['NEW']).order_by("order")
    context['waiving_logs'] = get_waivers_for_rg(result_group_object)

    context['defects_list_class'] = 'new'
    context['new_selected'] = "selected"

    return render(request, "waiving/waiver.html", context)


def remove_waiver(request, waiver_id):
    waiver = get_object_or_404(Waiver, id=waiver_id)
    sb = waiver.result_group.result.scanbinding
    wl = WaivingLog()
    wl.date = datetime.datetime.now()
    wl.state = WAIVER_LOG_ACTIONS['DELETE']
    wl.waiver = waiver
    wl.user = request.user
    wl.save()
    waiver.is_deleted = True
    waiver.save()
    Scan.objects.filter(id=sb.scan.id).update(
        last_access=datetime.datetime.now())
    if not waiver.is_comment():
        if sb.scan.is_waived() and not waiver_condition(waiver.result_group):
            ResultGroup.objects.filter(id=waiver.result_group.id).update(
                state=RESULT_GROUP_STATES['NEEDS_INSPECTION'])
            sb.scan.set_state(SCAN_STATES['DISPUTED'])
            if wl.user != waiver.user:
                scan_notification_email(request, sb.scan.id)
    request.session['status_message'] = \
        "%s (%s) invalidated." % (
        waiver.type_text,
        waiver.message[:50].rstrip() + '... ' if len(waiver.message) > 50
        else waiver.message)

    return HttpResponseRedirect(
        reverse('waiving/result',
                args=(waiver.result_group.result.scanbinding.id,))
    )


def fixed_defects(request, sb_id, result_group_id):
    """
    Display fixed defects
    """
    sb = get_object_or_404(ScanBinding, id=sb_id)
    context = get_result_context(request, sb)

    context['active_group'] = get_object_or_404(ResultGroup, id=result_group_id)
    context['defects'] = Defect.objects.filter(result_group=result_group_id,
                                               state=DEFECT_STATES['FIXED']).order_by("order")
    context['display_form'] = False
    context['display_waivers'] = False
    context['form_message'] = "This group can't be waived, because these \
defects are already fixed."
    context['fixed_selected'] = "selected"
    context['defects_list_class'] = "fixed"

    return render(request, "waiving/waiver.html", context)


def previously_waived(request, sb_id, result_group_id):
    """
    Display previously waived defects
    """
    sb = get_object_or_404(ScanBinding, id=sb_id)
    result_group_object = get_object_or_404(ResultGroup, id=result_group_id)

    context = {}

    if request.method == "POST":
        form = WaiverForm(request.POST)

        if form.is_valid():
            return waiver_post(form, request, sb, result_group_object,
                               'waiving/previously_waived', 'waiving/waiver',
                               "old_selected", "old")
        else:
            context['status_message'] = 'Invalid submission. For more ' \
                'details, see form.'
    else:
        form = WaiverForm()

    context.update(get_result_context(request, sb))

    w = get_last_waiver(result_group_object.checker_group,
                        sb.scan.package,
                        sb.scan.tag.release)

    if w:
        place_string = w.result_group.result.scanbinding.scan.nvr

        context['waivers_place'] = place_string
        context['matching_waiver'] = w

    context['active_group'] = ResultGroup.objects.get(id=result_group_id)
    context['defects'] = Defect.objects.filter(result_group=result_group_id,
                                               state=DEFECT_STATES['PREVIOUSLY_WAIVED']).order_by("order")
    context['waiving_logs'] = WaivingLog.objects.filter(
        waiver__result_group=result_group_id).exclude(
        state=WAIVER_LOG_ACTIONS['DELETE'])
    context['form'] = form
    context['display_form'] = True
    context['display_waivers'] = True
    context['old_selected'] = "selected"
    context['defects_list_class'] = "old"

    return render(request, "waiving/waiver.html", context)


def result(request, sb_id):
    """
    Display all the tests for specified scan
    """
    active_tab = request.session.pop("active_tab", "new_selected")
    context = get_result_context(request, get_object_or_404(ScanBinding,
                                                            id=sb_id))
    context[active_tab] = "selected"

    return render(request, "waiving/result.html", context)


def newest_result(request, package_name, release_tag):
    """
    Display latest result for specified package -- this is available on
     specific URL
    """
    try:
        sb = ScanBinding.objects.filter(
            scan__package__name=package_name,
            scan__tag__release__tag=release_tag,
            scan__enabled=True).latest()
    except ObjectDoesNotExist:
        raise Http404(f"No scans for package {package_name} and release {release_tag}")

    return HttpResponseRedirect(reverse("waiving/result", args=[sb.id]))


def _render_et_mapping(request, **kwargs):
    etm = get_object_or_404(ETMapping, **kwargs)
    if etm.latest_run is None:
        context = {'not_finished': etm.comment}
        return render(request, "waiving/result.html", context)

    return HttpResponseRedirect(reverse("waiving/result",
                                        args=[etm.latest_run.id]))


def etmapping_latest(request, etmapping_id):
    """
    Display latest result for etm_id
    """
    return _render_et_mapping(request, id=etmapping_id)


def et_latest(request, et_id):
    """
    Display latest result for etm_et_scan_id
    """
    return _render_et_mapping(request, et_scan_id=et_id)


def new_bz(request, package_id, release_id):
    """
    Create new bugzilla
    """
    package = get_object_or_404(Package, id=package_id)
    release = get_object_or_404(SystemRelease, id=release_id)
    if bugzilla.get_unreported_bugs(package, release):
        bugzilla.create_bug(request, package, release)
    return HttpResponseRedirect(reverse('waiving/result/newest',
                                        args=(package.name, release.tag)))


def update_bz(request, package_id, release_id):
    """
    update existing bugzilla
    """
    package = get_object_or_404(Package, id=package_id)
    release = get_object_or_404(SystemRelease, id=release_id)
    if bugzilla.get_unreported_bugs(package, release):
        bugzilla.update_bug(request, package, release)
    return HttpResponseRedirect(reverse('waiving/result/newest',
                                        args=(package.name, release.tag)))


def new_jira(request, package_id, release_id):
    """
    Create new jira bug
    """
    package = get_object_or_404(Package, id=package_id)
    release = get_object_or_404(SystemRelease, id=release_id)
    if jira.get_unreported_bugs(package, release):
        jira.create_bug(request, package, release)
    return HttpResponseRedirect(reverse('waiving/result/newest',
                                        args=(package.name, release.tag)))


def update_jira(request, package_id, release_id):
    """
    Update existing jira bug
    """
    package = get_object_or_404(Package, id=package_id)
    release = get_object_or_404(SystemRelease, id=release_id)
    if jira.get_unreported_bugs(package, release):
        jira.update_bug(request, package, release)
    return HttpResponseRedirect(reverse('waiving/result/newest',
                                        args=(package.name, release.tag)))
