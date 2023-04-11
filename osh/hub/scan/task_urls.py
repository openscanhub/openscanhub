"""custom task urls"""

from django.urls import path
from kobo.client.constants import TASK_STATES
from kobo.hub.views import TaskDetail, TaskListView, task_log, task_log_json

urlpatterns = [
    path("et/",
         TaskListView.as_view(title="Errata Tool Tasks", ),
         kwargs={'method': "ErrataDiffBuild"},
         name="task/et"),

    path("",
         TaskListView.as_view(),
         # kwargs={'method__in': ['DiffBuild', 'MockBuild', 'VersionDiffBuild']},
         name="task/index"),

    path("<int:pk>/",
         TaskDetail.as_view(),
         name="task/detail"),

    path("running/",
         TaskListView.as_view(
             title="Running Tasks",
             state=(
                 TASK_STATES["FREE"],
                 TASK_STATES["ASSIGNED"],
                 TASK_STATES["OPEN"]
             )
         ),
         name="task/running"),

    path("finished/",
         TaskListView.as_view(
             state=(
                 TASK_STATES["CLOSED"],
                 TASK_STATES["INTERRUPTED"],
                 TASK_STATES["CANCELED"],
                 TASK_STATES["FAILED"]
             ),
             title="Finished Tasks",
         ),
         kwargs={
             'method__in': [
                 'DiffBuild',
                 'MockBuild',
                 'VersionDiffBuild'
             ]
         },
         name="task/finished"),

    path("<int:id>/log/<path:log_name>",
         task_log,
         name="task/log"),

    path("<int:id>/log-json/<path:log_name>",
         task_log_json,
         name="task/log-json"),
]
