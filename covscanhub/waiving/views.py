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
    SystemRelease
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


def get_result_context(sb):
    logs = {}
    context = {}
    package = sb.scan.package
    release = sb.scan.tag.release
    unrep_waivers = get_unreported_bugs(package, release)

    file_labels = {
        'csdiff.html': 'Defects diff',
        'csdiff_fixed.html': 'Fixed defects diff',
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
        context['output_new'] = get_five_tuple(get_waiving_data(
            sb.result, DEFECT_STATES['NEW']))
        context['output_fixed'] = get_five_tuple(get_waiving_data(
            sb.result, DEFECT_STATES['FIXED']))
    elif sb.scan.state == SCAN_STATES['FAILED']:
        context['not_finished'] = "Scan failed. Please contact administrator."
    else:
        context['not_finished'] = "Scan haven't finished yet."
    context['sb'] = sb
    context['logs'] = logs
    context['compare_title'] = get_compare_title(
        sb.scan.nvr,
        sb.scan.base.nvr,
    )
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


def get_five_tuple(output):
    result_five_tuples = []
    i = 0
    while True:
        low_bound = 5 * i
        high_bound = 5 * (i + 1)
        if low_bound + 1 > len(output.keys()):
            break
        tmp = {}
        for k in output.keys()[low_bound:high_bound]:
            tmp[k] = output[k]
        result_five_tuples.append(tmp)
        i += 1
    return result_five_tuples


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


def waiver(request, sb_id, result_group_id):
    """
    Display waiver (for new defects) for specified result & group
    """
    context = {}

    sb = get_object_or_404(ScanBinding, id=sb_id)
    result_group_object = get_object_or_404(ResultGroup, id=result_group_id)

    if request.method == "POST":
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

                if not get_unwaived_rgs(sb.result):
                    s.state = SCAN_STATES['WAIVED']
            s.last_access = datetime.datetime.now()
            s.save()

            logger.info('Waiver submitted for resultgroup %s',
                        result_group_object)
            return HttpResponseRedirect(reverse('waiving/result',
                                                args=(sb.id,)))

    if result_group_object.is_previously_waived():
        w = get_last_waiver(result_group_object.checker_group,
                            sb.scan.package,
                            sb.scan.tag.release)

        place_string = w.result_group.result.scanbinding.scan.nvr

        context['waivers_place'] = place_string
        context['matching_waiver'] = w
        context['display_form'] = False
        context['display_waivers'] = False
    else:
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
    context = dict(context.items() + get_result_context(sb).items())

    context['active_group'] = result_group_object
    context['defects'] = Defect.objects.filter(result_group=result_group_id,
                                               state=DEFECT_STATES['NEW']).\
                                                   order_by("order")
    context['waiving_logs'] = WaivingLog.objects.filter(
        waiver__result_group=result_group_id).exclude(
        state=WAIVER_LOG_ACTIONS['DELETE'])

    logger.debug('Displaying waiver for sb %s, result-group %s',
                 sb, result_group_object)

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
        ResultGroup.objects.filter(id=waiver.result_group.id).update(
            state=RESULT_GROUP_STATES['NEEDS_INSPECTION'])
    return HttpResponseRedirect(reverse('waiving/result',
        args=(waiver.result_group.result.scanbinding.id,)))


def fixed_defects(request, sb_id, result_group_id):
    """
    Display fixed defects
    """
    sb = get_object_or_404(ScanBinding, id=sb_id)
    context = get_result_context(sb)

    context['active_group'] = ResultGroup.objects.get(id=result_group_id)
    context['defects'] = Defect.objects.filter(result_group=result_group_id,
                                               state=DEFECT_STATES['FIXED']).\
                                               order_by("order")
    context['display_form'] = False
    context['display_waivers'] = False
    context['form_message'] = "This group can't be waived, because these \
defects are already fixed."

    return render_to_response("waiving/waiver.html",
                              context,
                              context_instance=RequestContext(request))


def result(request, sb_id):
    """
    Display all the tests for specified scan
    """
    return render_to_response(
        "waiving/result.html",
        get_result_context(get_object_or_404(ScanBinding, id=sb_id)),
        context_instance=RequestContext(request)
    )


def newest_result(request, package_name, release_tag):
    """
    Display latest result for specified package -- this is available on
     specific URL
    """
    return render_to_response(
        "waiving/result.html",
        get_result_context(
            ScanBinding.objects.filter(
                scan__package__name=package_name,
                scan__tag__release__tag=release_tag,
                scan__enabled=True
            ).latest()
        ),
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
