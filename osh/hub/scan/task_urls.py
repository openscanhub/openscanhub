"""custom task urls"""

from django.urls import path
from kobo.hub.urls.task import urlpatterns
from kobo.hub.views import TaskListView

urlpatterns.append(
    path("et/",
         TaskListView.as_view(title="Errata Tool Tasks"),
         # FIXME: https://gitlab.cee.redhat.com/covscan/covscan/-/issues/125
         kwargs={'method': "ErrataDiffBuild"},
         name="task/et")
)
