# -*- coding: utf-8 -*-
"""custom task urls"""

from django.conf.urls import *
from kobo.client.constants import TASK_STATES

from kobo.hub.views import TaskListView, TaskDetail


urlpatterns = [
    url(r"^et/$",
        TaskListView.as_view(title="Errata Tool Tasks", ),
        kwargs={'method': "ErrataDiffBuild"},
        name="task/et"),

    url(r"^$",
        TaskListView.as_view(),
        #kwargs={'method__in': ['DiffBuild', 'MockBuild', 'VersionDiffBuild']},
        name="task/index"),

    url(r"^(?P<pk>\d+)/$",
        TaskDetail.as_view(),
        name="task/detail"),

    url(r"^running/$",
        TaskListView.as_view(title="Running Tasks", state=(TASK_STATES["FREE"], TASK_STATES["ASSIGNED"], TASK_STATES["OPEN"])),
        name="task/running"),

    url(r"^finished/$",
        TaskListView.as_view(state=(TASK_STATES["CLOSED"], TASK_STATES["INTERRUPTED"], TASK_STATES["CANCELED"], TASK_STATES["FAILED"]),
                             title="Finished Tasks",),
        kwargs={'method__in': ['DiffBuild', 'MockBuild', 'VersionDiffBuild']},
        name="task/finished"),

    url(r"^(?P<id>\d+)/log/(?P<log_name>.+)$",
        "kobo.hub.views.task_log",
        name="task/log"),

    url(r"^(?P<id>\d+)/log-json/(?P<log_name>.+)$",
        "kobo.hub.views.task_log_json",
        name="task/log-json"),
    ]
