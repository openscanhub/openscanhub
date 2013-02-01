# -*- coding: utf-8 -*-
"""custom task urls"""

from django.conf.urls.defaults import *
from kobo.client.constants import TASK_STATES


urlpatterns = patterns("",
    url(r"^task/et/$",
        "kobo.hub.views.task_list",
        kwargs={"state": None,
                "title": "ET Tasks",
                "order_by": ["-id"],
                'method': "ErrataDiffBuild"},
        name="task/et"),

    url(r"^$",
        "kobo.hub.views.task_list",
        kwargs={"state": None,
                "title": "All tasks",
                "order_by": ["-id"],
                'method__in': ['DiffBuild', 'MockBuild', 'VersionDiffBuild']},
        name="task/index"),

    url(r"^(?P<id>\d+)/$",
        "kobo.hub.views.task_detail",
        name="task/detail"),

    url(r"^running/$",
        "kobo.hub.views.task_list",
        kwargs={"state": (TASK_STATES["FREE"],
                          TASK_STATES["ASSIGNED"],
                          TASK_STATES["OPEN"]),
                "title": "Running tasks",
                "order_by": ["id"]},
        name="task/running"),

    url(r"^finished/$",
        "kobo.hub.views.task_list",
        kwargs={"state": (TASK_STATES["CLOSED"],
                          TASK_STATES["INTERRUPTED"],
                          TASK_STATES["CANCELED"],
                          TASK_STATES["FAILED"]),
                "title": "Finished tasks",
                "order_by": ["-dt_finished", "id"],
                'method__in': ['DiffBuild', 'MockBuild', 'VersionDiffBuild']},
        name="task/finished"),

    url(r"^(?P<id>\d+)/log/(?P<log_name>.+)$",
        "kobo.hub.views.task_log",
        name="task/log"),

    url(r"^(?P<id>\d+)/log-json/(?P<log_name>.+)$",
        "kobo.hub.views.task_log_json",
        name="task/log-json"),
)
