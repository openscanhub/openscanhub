# -*- coding: utf-8 -*-

import time

from models import StatResults, StatType
from covscanhub.scan.models import SystemRelease

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.utils import simplejson as json

from service import display_values_inline, display_values


def stats_list(request):
    st = StatType.objects.all()
    context = {}
    context['results'] = {}
    for s in st:
        context['results'][s] = display_values_inline(s)

    return render_to_response("stats/list.html",
                              context,
                              context_instance=RequestContext(request))


def stats_detail(request, stat_id):
    context = {}
    context['type'] = StatType.objects.get(id=stat_id)
    context['results'] = display_values(context['type'])
    
    return render_to_response("stats/detail.html",
                              context,
                              context_instance=RequestContext(request))    


def stats_detail_graph(request, stat_id):
    """
    Provide data for graph.
    """
    st = StatType.objects.get(id=stat_id)
    sr = StatResults.objects.filter(stat=stat_id)
    data = {}
    data['title_text'] = st.key
    data['subtitle_text'] = st.comment
    data['x_axis'] = []
    data['y_axis_title'] = 'Count'
    data['data'] = []

    time_format = "%b %e"

    if 'RELEASE' in st.key:
        tmp = {}        
        for s in SystemRelease.objects.all():
            tmp[s.tag] = []
            for result in sr.filter(release=s).order_by('-date'):
                tmp[s.tag].append(result.value)
                if result.date.strftime(time_format) not in data['x_axis']:
                    data['x_axis'].append(result.date.strftime(time_format))
                if len(tmp[s.tag]) >= 12: break
        for rel in tmp:
            data['data'].append({'name': rel, 'data': tmp[rel]})
    else:
        data['data'].insert(0, {})
        data['data'][0]['name'] = 'Global'
        data['data'][0]['data'] = []
        for result in sr.order_by('-date'):
            data['data'][0]['data'].append(result.value)
            if result.date.strftime(time_format) not in data['x_axis']:
                data['x_axis'].append(result.date.strftime(time_format))
            if len(data['data'][0]['data']) >= 12: break

    return HttpResponse(json.dumps(data),
                        content_type='application/javascript; charset=utf8')