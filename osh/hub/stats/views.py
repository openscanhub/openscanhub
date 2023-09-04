# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import json
from collections import OrderedDict

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from osh.hub.scan.models import SystemRelease
from osh.hub.stats.models import StatResults, StatType
from osh.hub.stats.service import display_values


def release_stats_list(request, release_id):
    release = get_object_or_404(SystemRelease, id=release_id)

    context = {
        'results': OrderedDict(
            (stattype, (stattype.display_value(release), stattype.detail_url(release)))
            for stattype in StatType.objects.filter(is_release_specific=True)
            .order_by('group', 'order')
        ),
        'title': f'Statistics - {release.product}.{release.release}'
    }
    return render(request, "stats/list.html", context)


def stats_list(request):
    release_ids = StatResults.objects.all().values_list(
        'release__id', flat=True).distinct()

    context = {
        'releases': SystemRelease.objects.filter(id__in=release_ids),
        'results': OrderedDict(
            (stattype, (stattype.display_value(), stattype.detail_url()))
            for stattype in StatType.objects.filter(is_release_specific=False)
            .order_by('group', 'order')
        ),
        'title': 'Statistics'
    }
    return render(request, "stats/list.html", context)


def release_stats_detail(request, release_id, stat_id):
    release = get_object_or_404(SystemRelease, id=release_id)
    stat_type = get_object_or_404(StatType, id=stat_id)

    context = {
        'json_url': reverse('stats/release/detail/graph', args=[stat_id, release_id]),
        'results': display_values(stat_type, release),
        'title': f'Statistics - {release.product}.{release.release} - {stat_type.short_comment}',
        'type': stat_type
    }
    return render(request, "stats/detail.html", context)


def stats_detail(request, stat_id):
    stat_type = get_object_or_404(StatType, id=stat_id)
    context = {
        'json_url': reverse('stats/detail/graph', args=[stat_id]),
        'results': display_values(stat_type),
        'title': f'Statistics - {stat_type.short_comment}',
        'type': stat_type
    }
    return render(request, "stats/detail.html", context)


def stats_detail_graph(request, stat_id, release_id=None):
    """
    Provide data for graph.
    """
    st = get_object_or_404(StatType, id=stat_id)

    if release_id is not None:
        release = get_object_or_404(SystemRelease, id=release_id)
        label = release.tag
        sr = StatResults.objects.filter(stat=st, release=release)
    else:
        label = 'Global'
        sr = StatResults.objects.filter(stat=st)

    data = {
        'title': st.short_comment,
        'subtitle': st.comment,
        'label': label,
        'x': [],
        'y': [],
    }

    for result in sr.order_by('-date')[:12]:
        data['x'].append(result.date.strftime("%Y-%m-%d"))
        data['y'].append(result.value)

    return HttpResponse(json.dumps(data).encode(),
                        content_type='application/json; charset=utf8')
