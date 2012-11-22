# -*- coding: utf-8 -*-

from models import StatResults, StatType
from covscanhub.scan.models import SystemRelease

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.utils import simplejson as json
from django.utils.datastructures import SortedDict

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
    data['title'] = st.key
    data['subtitle'] = st.comment
    data['data'] = []

    time_format = "%Y-%m-%d"

    if 'RELEASE' in st.key:
        tmp = {} 
        tmp_labels = {}
        for s in SystemRelease.objects.all():
            # tmp = { date: { release: value } }
            tmp_labels[s.tag] = chr(ord('a') + len(tmp_labels.keys()))
            for result in sr.filter(release=s).order_by('date'):
                if result.date not in tmp:
                    tmp[result.date] = {}
                tmp[result.date][s.tag] = result.value

                if len(tmp.keys()) >= 12: break
            
        for rel in tmp:
            # data['data'] = [{x: date, a: 1, b: 2,...}]
            # data['labels'] = ['rhel-7.0','rhel-6.4',...]
            date_record = SortedDict({'x': rel.strftime(time_format)})
            for rel_tag in tmp[rel]:
                date_record[tmp_labels[rel_tag]] = tmp[rel][rel_tag]
            data['data'].append(date_record)
        data['ykeys'] = tmp_labels.values()
        data['labels'] = tmp_labels.keys()
    else:
        data['labels'] = ['Global']
        data['ykeys'] = ['a']
        for result in sr.order_by('date'):
            data['data'].append(
                {'x': result.date.strftime(time_format), 'a': result.value}
            )
            if len(data['data']) >= 12: break

    return HttpResponse(json.dumps(data),
                        content_type='application/javascript; charset=utf8')