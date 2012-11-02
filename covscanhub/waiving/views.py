# -*- coding: utf-8 -*-


import datetime
import os

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from kobo.django.views.generic import object_list

from covscanhub.scan.models import Scan

from models import CheckerGroup, Result, Defect, Event, Waiver, WAIVER_TYPES
from forms import WaiverForm
from service import get_missing_waivers


def get_result_context(request, result_object):
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
    context['unwaived_groups'] = get_missing_waivers(result_object)
    context['logs'] = logs
    
    return context


def get_waiving_data(result_id):
    defects = Defect.objects.filter(result=result_id)

    # TODO filter only "active" groups -- there might be some experimental/etc.
    groups = CheckerGroup.objects.all()

    output = {}

    # {group: number of defects}
    # TODO change value to (count, state={i, have, no, idea})
    for group in groups:
        output[group] = defects.filter(checker__group=group).count()
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


def waiver(request, result_id, checker_group_id):
    """
    Display waiver for specified scan and test
    """
    context = {}

    result_object = Result.objects.get(id=result_id)
    checker_group = CheckerGroup.objects.get(id=checker_group_id)

    if request.method == "POST":
        form = WaiverForm(request.POST)
        if form.is_valid():
            w = Waiver()
            w.date = datetime.datetime.now()
            w.message = form.cleaned_data['message']
            w.result = result_object
            w.group = checker_group
            w.user = request.user
            w.state = WAIVER_TYPES[form.cleaned_data['waiver_type']]
            w.save()

            s = Scan.objects.get(id=result_object.scan.id)

            s.last_access = datetime.datetime.now()
            s.save()
            return HttpResponseRedirect(reverse('waiving/result',
                                                args=(result_id,)))
    else:
        form = WaiverForm()
        context['form'] = form

    defects = {}

    for defect in Defect.objects.filter(checker__group__id=checker_group_id).\
            filter(result=result_id):
        defects[defect] = Event.objects.filter(defect=defect)

    context += get_result_context(request, result_object)

    context['group'] = checker_group
    context['defects'] = defects
    context['waivers'] = Waiver.objects.filter(group=checker_group).\
        filter(result=result_object)

    return render_to_response("waiving/waiver.html",
                              context,
                              context_instance=RequestContext(request))


def result(request, result_id):
    """
    Display all the tests for specified scan
    """
    return render_to_response(
        "waiving/result.html",
        context=get_result_context(request, Result.objects.get(id=result_id)),
        context_instance=RequestContext(request)
    )