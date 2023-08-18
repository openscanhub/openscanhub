# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from django.urls import path

from osh.hub.stats import views

urlpatterns = [
    path("",
         views.stats_list,
         name="stats/list"),
    path("<int:stat_id>/",
         views.stats_detail,
         name="stats/detail"),

    path("release/<int:release_id>/",
         views.release_stats_list,
         name="stats/release/list"),
    path("release/<int:release_id>/<int:stat_id>/",
         views.release_stats_detail,
         name="stats/release/detail"),

    path("<int:stat_id>/graph/",
         views.stats_detail_graph,
         name="stats/detail/graph"),
    path("<int:stat_id>/<int:release_id>/graph/",
         views.stats_detail_graph,
         name="stats/release/detail/graph"),
]
