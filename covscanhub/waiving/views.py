# -*- coding: utf-8 -*-

import datetime
import os
import logging

from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist

from kobo.django.views.generic import object_list

from covscanhub.scan.models import SCAN_STATES, ScanBinding, Package,\
    SystemRelease, ETMapping
from covscanhub.scan.compare import get_compare_title
from covscanhub.scan.service import get_latest_sb_by_package

from covscanhub.other.shortcuts import get_or_none

from covscanhub.waiving.bugzilla_reporting import create_bugzilla, \
    get_unreported_bugs, update_bugzilla
from covscanhub.waiving.models import *
from covscanhub.waiving.forms import WaiverForm
from covscanhub.waiving.service import get_unwaived_rgs, get_last_waiver, \
    display_in_result, get_defects_diff_display, waiver_condition


logger = logging.getLogger(__name__)


def get_result_context(request, sb):
    logs = {}
    context = {}
    package = sb.scan.package
    release = sb.scan.tag.release
    unrep_waivers = get_unreported_bugs(package, release)

    file_labels = {
        'csdiff.html': 'Added defects',
        'csdiff_fixed.html': 'Fixed defects',
        '.err': 'Complete defects output',
        'stdout.log': 'Log',
    }
    for i in sb.task.logs.list:
        basename = os.path.basename(i)
        for path, label in file_labels.iteritems():
            if basename.endswith(path):
                logs[i] = label
    #logs.sort(lambda x, y: cmp(os.path.split(x), os.path.split(y)))
    context['bugzilla'] = get_or_none(Bugzilla,
                                      package=package,
                                      release=release)
    if unrep_waivers:
        context['unreported_bugs_count'] = unrep_waivers.count()
    else:
        context['unreported_bugs_count'] = 0

    if sb.result:
        new_defects = get_tupled_data(get_waiving_data(
            sb.result, defect_type=DEFECT_STATES['NEW']))
        fixed_defects = get_tupled_data(get_waiving_data(
            sb.result, defect_type=DEFECT_STATES['FIXED']))
        old_defects = get_tupled_data(get_waiving_data(
            sb.result, defect_type=DEFECT_STATES['PREVIOUSLY_WAIVED']))
        context['output_new'] = new_defects
        context['output_fixed'] = fixed_defects
        context['output_old'] = old_defects
    elif sb.scan.state == SCAN_STATES['FAILED']:
        context['not_finished'] = "Scan failed. Please contact administrator."
    else:
        context['not_finished'] = "Scan not complete."
    context['sb'] = sb
    context['logs'] = logs
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
    context['first_sb'] = sb.scan.get_first_scan_binding()
    context['newest_sb'] = \
        get_latest_sb_by_package(sb.scan.tag, sb.scan.package)
    context['previous_sb'] = getattr(sb.scan.get_child_scan(),
                                     'scanbinding', None)
    context['next_sb'] = getattr(sb.scan.parent, 'scanbinding', None)
    return context


def get_waiving_data(result_object, defect_type):
    """return list of checker_groups with states and counts"""
    output = {}

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
            view_data = display_in_result(rg)
            view_data['id'] = rg.id
            output[group] = view_data
    return output


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
    Display list of all target results
    """
    args = {
        # order by scan__date, because result might not exist
        "queryset": ScanBinding.objects.exclude(
            scan__base__isnull=True).order_by('-scan__date_submitted'),
        "allow_empty": True,
        "paginate_by": 50,
        "template_name": "waiving/list.html",
        "template_object_name": "scanbinding",
        "extra_context": {
            "title": "List of all results",
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

        prim_url = reverse(url_name, args=(sb.id, ),
                           kwargs={'active_tab': active_tab,
                                   "defects_list_class": defects_list_class})

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


def waiver(request, sb_id, result_group_id, active_tab="new_selected",
           defects_list_class="new"):
    """
    Display waiver (for new defects) for specified result & group
    """
    context = {}

    sb = get_object_or_404(ScanBinding, id=sb_id)
    result_group_object = get_object_or_404(ResultGroup, id=result_group_id)

    if request.method == "POST":
        return waiver_post(request, sb, result_group_object, "waiving/result",
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

    context['defects_list_class'] = defects_list_class
    context[active_tab] = "selected"

    return render_to_response("waiving/waiver.html",
                              context,
                              context_instance=RequestContext(request))


def remove_waiver(request, waiver_id):
    waiver = get_object_or_404(Waiver, id=waiver_id)
    wl = WaivingLog()
    wl.date = datetime.datetime.now()
    wl.state = WAIVER_LOG_ACTIONS['DELETE']
    wl.waiver = waiver
    wl.user = request.user
    wl.save()
    waiver.is_deleted = True
    waiver.save()
    if not waiver_condition(waiver.result_group):
        sb = waiver.result_group.result.scanbinding
        ResultGroup.objects.filter(id=waiver.result_group.id).update(
            state=RESULT_GROUP_STATES['NEEDS_INSPECTION'])
        sb.scan.set_state(SCAN_STATES['DISPUTED'])
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
    Display fixed defects
    """
    sb = get_object_or_404(ScanBinding, id=sb_id)
    result_group_object = get_object_or_404(ResultGroup, id=result_group_id)

    if request.method == "POST":
        result_group_object.defect_type = DEFECT_STATES['NEW']
        result_group_object.save()
        return waiver_post(request, sb, result_group_object, "waiving/result",
                           'waiving/previously_waived', "old_selected", "old")

    context = get_result_context(request, sb)

    w = get_last_waiver(result_group_object.checker_group,
                        sb.scan.package,
                        sb.scan.tag.release)

    place_string = w.result_group.result.scanbinding.scan.nvr

    context['waivers_place'] = place_string
    context['matching_waiver'] = w

    context['active_group'] = ResultGroup.objects.get(id=result_group_id)
    context['defects'] = Defect.objects.filter(result_group=result_group_id,
                                               state=DEFECT_STATES['NEW']).\
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
    context = get_result_context(request, get_object_or_404(ScanBinding,
                                                            id=sb_id))
    context['new_selected'] = "selected"
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
