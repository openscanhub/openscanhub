"""
    TODO Once on 1.5, use filter from django.contrib.humanize
"""

import json
from collections import OrderedDict

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse

from osh.hub.scan.models import SystemRelease

from .models import StatResults, StatType
from .service import display_values


def release_list(request, release_id):
    context = {}
    context['release'] = SystemRelease.objects.get(id=release_id)

    context['results'] = OrderedDict()
    for stattype in StatType.objects.filter(is_release_specific=True).\
            order_by('group', 'order'):
        context['results'][stattype] = stattype.display_value(
            context['release']), stattype.detail_url(context['release'])

    return render(request, "stats/list.html", context)


def stats_list(request):
    context = {}
    int_releases = StatResults.objects.all().values_list(
        'release__id', flat=True).distinct()
    context['releases'] = SystemRelease.objects.filter(id__in=int_releases)

    print(context['releases'])
    context['results'] = OrderedDict()
    for stattype in StatType.objects.filter(is_release_specific=False).\
            order_by('group', 'order'):
        context['results'][stattype] = stattype.display_value(), \
            stattype.detail_url()

    return render(request, "stats/list.html", context)


def release_stats_detail(request, release_id, stat_id):
    context = {}
    context['release'] = SystemRelease.objects.get(id=release_id)
    context['type'] = StatType.objects.get(id=stat_id)
    context['results'] = display_values(context['type'], context['release'])
    context['json_url'] = reverse('stats/release/detail/graph',
                                  kwargs={'stat_id': stat_id,
                                          'release_id': release_id, })

    return render(request, "stats/detail.html", context)


def stats_detail(request, stat_id):
    context = {}
    context['type'] = StatType.objects.get(id=stat_id)
    context['results'] = display_values(context['type'])
    context['json_url'] = reverse('stats/detail/graph',
                                  kwargs={'stat_id': stat_id})
    return render(request, "stats/detail.html", context)


def stats_detail_graph(request, stat_id, release_id=None):
    """
    View for AJAX
    Provide data for graph.
    """
    if release_id is not None:
        release = SystemRelease.objects.get(id=release_id)
        label = release.tag
        sr = StatResults.objects.filter(stat=stat_id, release=release)
    else:
        label = 'Global'
        sr = StatResults.objects.filter(stat=stat_id)

    st = StatType.objects.get(id=stat_id)
    data = {}
    data['title'] = st.short_comment
    data['subtitle'] = st.comment
    data['data'] = []

    time_format = "%Y-%m-%d"

    data['labels'] = [label]
    data['ykeys'] = ['a']
    for result in sr.order_by('-date'):
        data['data'].append(
            {'x': result.date.strftime(time_format), 'a': result.value}
        )
        if len(data['data']) >= 12:
            break
    return HttpResponse(json.dumps(data).encode(),
                        content_type='application/javascript; charset=utf8')


""" stats from all releases added to graph
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
    date_record = OrderedDict({'x': rel.strftime(time_format)})
    for rel_tag in tmp[rel]:
        date_record[tmp_labels[rel_tag]] = tmp[rel][rel_tag]
    data['data'].append(date_record)
data['ykeys'] = tmp_labels.values()
data['labels'] = tmp_labels.keys()
"""
