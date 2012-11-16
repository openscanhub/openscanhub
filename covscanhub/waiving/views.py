# -*- coding: utf-8 -*-


import datetime
import os
import logging

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist

from kobo.django.views.generic import object_list

from covscanhub.scan.models import Scan, SCAN_STATES

from models import CheckerGroup, Result, ResultGroup, Defect, Event, Waiver,\
    WAIVER_TYPES, DEFECT_STATES, RESULT_GROUP_STATES
from forms import WaiverForm
from service import get_unwaived_rgs, get_last_waiver

logger = logging.getLogger(__name__)


def get_result_context(result_object):
    logs = {}
    context = {}
    # fixed_html_file = 'csdiff_fixed.html'
    # html_file = 'csdiff.html'
    file_labels = {
        'csdiff.html': 'Defects diff',
        'csdiff_fixed.html': 'Fixed defects diff',
        '.err': 'Complete defects output',
    }
    for i in result_object.scan.task.logs.list:
        basename = os.path.basename(i)
        for path, label in file_labels.iteritems():
            if basename.endswith(path):
                logs[i] = label
    #logs.sort(lambda x, y: cmp(os.path.split(x), os.path.split(y)))

    context['output'] = get_five_tuple(get_waiving_data(result_object.id))
    context['result'] = result_object
    context['logs'] = logs

    return context


def get_waiving_data(result_id):
    output = {}

    # checker_group: result_group
    for group in CheckerGroup.objects.filter(enabled=True):
        try:
            output[group] = ResultGroup.objects.get(checker_group=group,
                                                    result=result_id)
        except ObjectDoesNotExist:
            output[group] = None
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
        "queryset": Result.objects.all().exclude(scan__base__isnull=True),
        "allow_empty": True,
        "paginate_by": 50,
        "template_name": "waiving/list.html",
        "template_object_name": "result",
        "extra_context": {
            "title": "List of all results",
        }
    }
    return object_list(request, **args)


def waiver(request, result_id, result_group_id):
    """
    Display waiver (for new defects) for specified result & group
    """
    context = {}

    result_object = Result.objects.get(id=result_id)
    result_group_object = ResultGroup.objects.get(id=result_group_id)

    if request.method == "POST":
        form = WaiverForm(request.POST)
        if form.is_valid():
            w = Waiver()
            w.date = datetime.datetime.now()
            w.message = form.cleaned_data['message']
            w.result_group = result_group_object
            w.user = request.user
            w.state = WAIVER_TYPES[form.cleaned_data['waiver_type']]
            w.save()

            s = Scan.objects.get(id=result_object.scan.id)

            s.last_access = datetime.datetime.now()
            s.save()

            result_group_object.state = RESULT_GROUP_STATES['WAIVED']
            result_group_object.save()

            if not get_unwaived_rgs(result_object):
                result_object.scan.state = SCAN_STATES['WAIVED']

            logger.info('Waiver submitted for resultgroup %s',
                        result_group_object)
            return HttpResponseRedirect(reverse('waiving/result',
                                                args=(result_id,)))

    if result_group_object.is_previously_waived():
        w = get_last_waiver(result_group_object.checker_group,
                            result_group_object.result.scan.package,
                            result_group_object.result.scan.tag.release)

        place_string = "Scan: target = %s, base = %s" % (
            w.result_group.result.scan.nvr,
            w.result_group.result.scan.base.nvr,
        )
        context['waivers_place'] = place_string
        context['waivers_result'] = w.result_group.result.id
        context['display_form'] = False
        context['display_waivers'] = True
    else:
        form = WaiverForm()
        context['form'] = form
        context['display_form'] = True
        context['display_waivers'] = True

    defects = {}

    for defect in Defect.objects.filter(result_group=result_group_id,
                                        state=DEFECT_STATES['NEW']):
        defects[defect] = Event.objects.filter(defect=defect)

    # merge already created context with result context
    context = dict(context.items() + get_result_context(result_object).items())

    context['group'] = result_group_object
    context['defects'] = defects
    context['waivers'] = Waiver.objects.filter(result_group=result_group_id)

    logger.debug('Displaying waiver for result %s, result-group %s',
                 result_object, result_group_object)

    return render_to_response("waiving/waiver.html",
                              context,
                              context_instance=RequestContext(request))


def fixed_defects(request, result_id, result_group_id):
    """
    Display fixed defects
    """
    defects = {}
    context = get_result_context(Result.objects.get(id=result_id))

    for defect in Defect.objects.filter(result_group=result_group_id,
                                        state=DEFECT_STATES['FIXED']):
        defects[defect] = Event.objects.filter(defect=defect)

    context['group'] = ResultGroup.objects.get(id=result_group_id)
    context['defects'] = defects
    context['display_form'] = False
    context['display_waivers'] = False

    return render_to_response("waiving/waiver.html",
                              context,
                              context_instance=RequestContext(request))


def result(request, result_id):
    """
    Display all the tests for specified scan
    """
    return render_to_response(
        "waiving/result.html",
        get_result_context(Result.objects.get(id=result_id)),
        context_instance=RequestContext(request)
    )