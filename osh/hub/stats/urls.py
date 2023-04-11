from django.conf.urls import url

import osh.hub.stats.views

urlpatterns = [
    url(r"^$",
        osh.hub.stats.views.stats_list,
        name="stats/list"),
    url(r"^(?P<stat_id>\d+)/$",
        osh.hub.stats.views.stats_detail,
        name="stats/detail"),

    url(r"^release/(?P<release_id>\d+)/$",
        osh.hub.stats.views.release_list,
        name="stats/release/list"),
    url(r"^release/(?P<release_id>\d+)/(?P<stat_id>\d+)/$",
        osh.hub.stats.views.release_stats_detail,
        name="stats/release/detail"),

    url(r"^(?P<stat_id>\d+)/graph/$",
        osh.hub.stats.views.stats_detail_graph,
        name="stats/detail/graph"),
    url(r"^(?P<stat_id>\d+)/(?P<release_id>\d+)/graph/$",
        osh.hub.stats.views.release_stats_detail_graph,
        name="stats/release/detail/graph"),
]
