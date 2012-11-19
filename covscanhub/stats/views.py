# -*- coding: utf-8 -*-

from models import StatResults, StatType

from django.shortcuts import render_to_response


def stats_list(request):
    st = StatType.objects.all()
    context = {}
    context['results'] = {}
    for s in st:
        context['results'][s] = StatResults.objects.filter(stat=s)
            .latest().display_value()

    return render_to_response("stats/list.html",
                              context,
                              context_instance=RequestContext(request))


def stats_detail(request, stat_id):
    context = {}
    context['type'] = StatType.objects.get(id=stat_id)
    context['result'] = StatResults.objects.filter(stat=stat_id)
    
    return render_to_response("stats/detail.html",
                              context,
                              context_instance=RequestContext(request))    