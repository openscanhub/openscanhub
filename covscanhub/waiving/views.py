# -*- coding: utf-8 -*-

import datetime
import os
import logging
import urllib

from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist

from kobo.django.views.generic import object_list

from covscanhub.scan.models import SCAN_STATES, ScanBinding, Package,\
    SystemRelease, ETMapping, Scan
from covscanhub.scan.compare import get_compare_title
from covscanhub.scan.service import get_latest_sb_by_package

from covscanhub.other.shortcuts import get_or_none
from covscanhub.other.constants import *

from covscanhub.waiving.bugzilla_reporting import create_bugzilla, \
    get_unreported_bugs, update_bugzilla
from covscanhub.waiving.models import *
from covscanhub.waiving.forms import WaiverForm, ScanListSearchForm
from covscanhub.waiving.service import get_unwaived_rgs, get_last_waiver, \
    display_in_result, get_defects_diff_display, waiver_condition


logger = logging.getLogger(__name__)


def get_result_context(request, sb):
    #logs = {}
    #context = {}
    package = sb.scan.package
    release = sb.scan.tag.release
    unrep_waivers = get_unreported_bugs(package, release)

    context = add_logs_to_context(sb)
    context['bugzilla'] = get_or_none(Bugzilla,
                                      package=package,
                                      release=release)
    if unrep_waivers:
        context['unreported_bugs_count'] = unrep_waivers.count()
    else:
        context['unreported_bugs_count'] = 0

    if sb.result:
        n_out, n_count = get_waiving_data(sb.result,
                                          defect_type=DEFECT_STATES['NEW'])
        new_defects = get_tupled_data(n_out)

        f_out, f_count = get_waiving_data(sb.result,
                                          defect_type=DEFECT_STATES['FIXED'])
        fixed_defects = get_tupled_data(f_out)

        o_out, o_count = get_waiving_data(sb.result,
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
        context['not_finished'] = "Scan failed. Please contact administrator."
    elif sb.scan.state == SCAN_STATES['CANCELED']:
        context['not_finished'] = "Scan is canceled (is superseded by newer one)."
    else:
        context['not_finished'] = "Scan not complete."
    context['sb'] = sb
    context['compare_title'] = get_compare_title(
        sb.scan.nvr,
        sb.scan.base.nvr,
    )
    if 'status_message' in request.session:
        context['status_message'] = request.session.pop('status_message')
    context['title'] = "%s compared to %s" % (
        sb.scan.nvr,
        sb.scan.base.nvr,
    )

    # links for other runs
    context['first_sb'] = sb.scan.get_first_scan_binding()
    context['newest_sb'] = \
        get_latest_sb_by_package(sb.scan.tag.release, sb.scan.package)
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
    log_prefix = os.path.join(sb.scan.nvr, 'run1', sb.scan.nvr)

    logs.append(create_log_dict('Added defects', 'Add_32.png',
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
                                sb.scan.nvr + '.html',
                                [(log_prefix + '.err', 'TXT'),
                                 (sb.scan.nvr + '.html', 'HTML'),
                                 (log_prefix + '.js', 'JSON')], logs_list))
    logs.append(create_log_dict('Scan Log', 'Message_log_32.png',
                                'stdout.log',
                                [('stdout.log', 'TXT')], logs_list))

    """
    for i in sb.task.logs.list:
        basename = os.path.basename(i)
        for path, label in file_labels.iteritems():
            if basename.endswith(path):
                logs[i] = label
    context['logs'] = logs
    """
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
            output[group] = get_defects_diff_display(checker_group=group,
                                                     result=result_object,
                                                     defect_type=defect_type)
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
    if len(output.keys()) % 4 == 0:
        column_count = 4
    else:
        column_count = 5
    while True:
        low_bound = column_count * i
        high_bound = column_count * (i + 1)
        if low_bound + 1 > len(output.keys()):
            break
        tmp = {}
        for k in output.keys()[low_bound:high_bound]:
            tmp[k] = output[k]
        result_tuples.append(tmp)
        i += 1
    return result_tuples


def results_list(request):
    """
    Display list of all target results; request['GET'] may contain order_by
    """
    order_by = request.GET.get('order_by', None)
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

        order = order_prefix + order_by_mapping[order_by]
    else:
        order = '-scan__date_submitted'

    # link definitions to template
    table_sort = {}
    for o in order_by_mapping.iterkeys():
        t = request.GET.copy()
        if order_by == o and not order_prefix:
            t[u'order_by'] = '-' + o
            url = urllib.urlencode(t)
            table_sort[o] = u'?' + url if url else u'', 'down'
        else:
            t[u'order_by'] = o
            url = urllib.urlencode(t)
            table_sort[o] = u'?' + url if url else u'', 'up'

    search_form = ScanListSearchForm(request.GET)
    # order by scan__date, because result might not exist
    q = ScanBinding.objects.exclude(
        scan__base__isnull=True).filter(
            search_form.get_query(request)).order_by(order)
    if search_form.extra_query():
        q_ids = search_form.objects_satisfy(q)
        q = q.filter(id__in=q_ids)

    args = {
        "queryset": q,
        "allow_empty": True,
        "paginate_by": 50,
        "template_name": "waiving/list.html",
        "template_object_name": "scanbinding",
        "extra_context": {
            "title": "List of all results",
            "search_form": search_form,
            "table_sort": table_sort,
        }
    }
    return object_list(request, **args)


def waiver_post(request, sb, result_group_object, url_name, url_name_next,
                active_tab, defects_list_class):
    form = WaiverForm(request.POST)
    if form.is_valid():
        wl = WaivingLog()
        wl.user = request.user
        wl.date = datetime.datetime.now()
        if result_group_object.has_waiver():
            wl.state = WAIVER_LOG_ACTIONS['REWAIVE']
        else:
            wl.state = WAIVER_LOG_ACTIONS['NEW']
        w = Waiver()
        w.date = datetime.datetime.now()
        w.message = form.cleaned_data['message']
        w.result_group = result_group_object
        w.user = request.user
        w.state = WAIVER_TYPES[form.cleaned_data['waiver_type']]
        w.save()

        wl.waiver = w
        wl.save()

        s = sb.scan
        if waiver_condition(result_group_object):
            result_group_object.state = RESULT_GROUP_STATES['WAIVED']
            result_group_object.save()

            if not get_unwaived_rgs(sb.result) and not s.is_waived():
                s.set_state(SCAN_STATES['WAIVED'])
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

        prim_url = reverse("waiving/result", args=(sb.id, ))
        rgs = get_unwaived_rgs(result_group_object.result)
        if not rgs:
            request.session['status_message'] += " Everything is waived."
        if 'submit_next' in request.POST:
            if rgs:
                return HttpResponseRedirect(reverse(url_name_next,
                                                    args=(sb.id, rgs[0].id)))
        return HttpResponseRedirect(prim_url)
    else:
        request.session['status_message'] = "You have entered invalid data."
        return HttpResponseRedirect(prim_url)


def waiver(request, sb_id, result_group_id):
    """
    Display waiver (for new defects) for specified result & group
    """
    context = {}

    sb = get_object_or_404(ScanBinding, id=sb_id)
    result_group_object = get_object_or_404(ResultGroup, id=result_group_id)

    if request.method == "POST":
        return waiver_post(request, sb, result_group_object, 'waiving/waiver',
                           'waiving/waiver', "new_selected", "new")

    # this could help user to determine if this is FP or not
    previous_waivers = result_group_object.previous_waivers()
    if previous_waivers:
        context['previous_waivers'] = previous_waivers
    context['display_waivers'] = True
    if sb.scan.enabled:
        form = WaiverForm()
        context['form'] = form
        context['display_form'] = True
    else:
        context['display_form'] = False
        context['form_message'] = 'This is not the newest scan.'

    # merge already created context with result context
    context = dict(context.items() + get_result_context(request, sb).items())

    context['active_group'] = result_group_object
    context['defects'] = Defect.objects.filter(result_group=result_group_id,
                                               state=DEFECT_STATES['NEW']).\
                                                   order_by("order")
    context['waiving_logs'] = WaivingLog.objects.filter(
        waiver__result_group=result_group_id).exclude(
        state=WAIVER_LOG_ACTIONS['DELETE'])

    logger.debug('Displaying waiver for sb %s, result-group %s',
                 sb, result_group_object)

    context['defects_list_class'] = 'new'
    context['new_selected'] = "selected"
    return render_to_response("waiving/waiver.html",
                              context,
                              context_instance=RequestContext(request))


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
    if not waiver_condition(waiver.result_group):

        ResultGroup.objects.filter(id=waiver.result_group.id).update(
            state=RESULT_GROUP_STATES['NEEDS_INSPECTION'])
        sb.scan.set_state(SCAN_STATES['DISPUTED'])
    request.session['status_message'] = \
        "Waiver (%s) invalidated." % (
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

    context['active_group'] = ResultGroup.objects.get(id=result_group_id)
    context['defects'] = Defect.objects.filter(result_group=result_group_id,
                                               state=DEFECT_STATES['FIXED']).\
                                               order_by("order")
    context['display_form'] = False
    context['display_waivers'] = False
    context['form_message'] = "This group can't be waived, because these \
defects are already fixed."
    context['fixed_selected'] = "selected"
    context['defects_list_class'] = "fixed"
    return render_to_response("waiving/waiver.html",
                              context,
                              context_instance=RequestContext(request))


def previously_waived(request, sb_id, result_group_id):
    """
    Display previously waived defects
    """
    sb = get_object_or_404(ScanBinding, id=sb_id)
    result_group_object = get_object_or_404(ResultGroup, id=result_group_id)

    if request.method == "POST":
        result_group_object.defect_type = DEFECT_STATES['PREVIOUSLY_WAIVED']
        result_group_object.save()
        return waiver_post(request, sb, result_group_object,
                           'waiving/previously_waived', 'waiving/waiver',
                           "old_selected", "old")

    context = get_result_context(request, sb)

    w = get_last_waiver(result_group_object.checker_group,
                        sb.scan.package,
                        sb.scan.tag.release)

    place_string = w.result_group.result.scanbinding.scan.nvr

    context['waivers_place'] = place_string
    context['matching_waiver'] = w

    context['active_group'] = ResultGroup.objects.get(id=result_group_id)
    context['defects'] = Defect.objects.filter(result_group=result_group_id,
                                               state=DEFECT_STATES['PREVIOUSLY_WAIVED']).\
                                               order_by("order")
    form = WaiverForm()
    context['form'] = form
    context['display_form'] = True
    context['display_waivers'] = True
    context['old_selected'] = "selected"
    context['defects_list_class'] = "old"
    return render_to_response("waiving/waiver.html",
                              context,
                              context_instance=RequestContext(request))


def result(request, sb_id):
    """
    Display all the tests for specified scan
    """
    active_tab = request.session.pop("active_tab", "new_selected")
    context = get_result_context(request, get_object_or_404(ScanBinding,
                                                            id=sb_id))
    context[active_tab] = "selected"
    return render_to_response(
        "waiving/result.html",
        context,
        context_instance=RequestContext(request)
    )


def newest_result(request, package_name, release_tag):
    """
    Display latest result for specified package -- this is available on
     specific URL
    """
    context = get_result_context(request, ScanBinding.objects.filter(
        scan__package__name=package_name,
        scan__tag__release__tag=release_tag,
        scan__enabled=True).latest()
    )
    context['new_selected'] = "selected"
    return render_to_response(
        "waiving/result.html",
        context,
        context_instance=RequestContext(request)
    )


def etmapping_latest(request, etmapping_id):
    """
    url(r"^et_mapping/(?P<etmapping_id>\d+)/$",
        "covscanhub.waiving.views.etmapping_latest",
        name="waiving/etmapping_id"),

    Display latest result for et_internal_covscan_id
    """
    context = get_result_context(
        request,
        ETMapping.objects.get(id=etmapping_id).latest_run
    )
    context['new_selected'] = "selected"
    return render_to_response(
        "waiving/result.html",
        context,
        context_instance=RequestContext(request)
    )


def et_latest(request, et_id):
    """
    url(r"^et/(?P<et_id>.+)/$",
        "covscanhub.waiving.views.et_latest",
        name="waiving/et_id"),

    Display latest result for et_internal_covscan_id
    """
    context = get_result_context(
        request,
        ETMapping.objects.get(et_scan_id=et_id).latest_run
    )
    context['new_selected'] = "selected"
    return render_to_response(
        "waiving/result.html",
        context,
        context_instance=RequestContext(request)
    )


def new_bz(request, package_id, release_id):
    """
    Create new bugzilla
    """
    package = get_object_or_404(Package, id=package_id)
    release = get_object_or_404(SystemRelease, id=release_id)
    if get_unreported_bugs(package, release):
        create_bugzilla(request, package, release)
    return HttpResponseRedirect(reverse('waiving/result/newest',
                                        args=(package.name, release.tag)))


def update_bz(request, package_id, release_id):
    """
    update existing bugzilla
    """
    package = get_object_or_404(Package, id=package_id)
    release = get_object_or_404(SystemRelease, id=release_id)
    if get_unreported_bugs(package, release):
        update_bugzilla(request, package, release)
    return HttpResponseRedirect(reverse('waiving/result/newest',
                                        args=(package.name, release.tag)))
