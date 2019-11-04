# -*- coding: utf-8 -*-


from __future__ import absolute_import
from django.conf.urls import url
import covscanhub.stats.views

urlpatterns = [
    url(r"^$",
        covscanhub.stats.views.stats_list,
        name="stats/list"),
    url(r"^(?P<stat_id>\d+)/$",
        covscanhub.stats.views.stats_detail,
        name="stats/detail"),

    url(r"^release/(?P<release_id>\d+)/$",
        covscanhub.stats.views.release_list,
        name="stats/release/list"),
    url(r"^release/(?P<release_id>\d+)/(?P<stat_id>\d+)/$",
        covscanhub.stats.views.release_stats_detail,
        name="stats/release/detail"),
        
    url(r"^(?P<stat_id>\d+)/graph/$",
        covscanhub.stats.views.stats_detail_graph,
        name="stats/detail/graph"),
    url(r"^(?P<stat_id>\d+)/(?P<release_id>\d+)/graph/$",
        covscanhub.stats.views.release_stats_detail_graph,
        name="stats/release/detail/graph"),        
    ]
