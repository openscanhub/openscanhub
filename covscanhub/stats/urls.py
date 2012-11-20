# -*- coding: utf-8 -*-


from django.conf.urls.defaults import patterns, url


urlpatterns = patterns("",
    url(r"^$", "covscanhub.stats.views.stats_list", name="stats/list"),
    url(r"^(?P<stat_id>\d+)/$", "covscanhub.stats.views.stats_detail",
        name="stats/detail"),
    url(r"^(?P<stat_id>\d+)/graph/$",
        "covscanhub.stats.views.stats_detail_graph",
        name="stats/detail/graph"),
)