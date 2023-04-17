from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import TemplateView

admin.autodiscover()


urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="index"),
    path("", TemplateView.as_view(template_name="index.html"), name="home/index"),
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # path('admin/doc/', include('django.contrib.admindocs.urls')),

    path("auth/", include("kobo.hub.urls.auth")),
    path("task/", include("osh.hub.scan.task_urls")),
    path("info/arch/", include("kobo.hub.urls.arch")),
    path("info/channel/", include("kobo.hub.urls.channel")),
    path("info/user/", include("kobo.hub.urls.user")),
    path("info/worker/", include("kobo.hub.urls.worker")),
    path("waiving/", include("osh.hub.waiving.urls")),

    path("scan/", include("osh.hub.scan.urls")),

    path("stats/", include("osh.hub.stats.urls")),

    path('admin/', admin.site.urls),

    # Include kobo hub xmlrpc module urls:
    path("xmlrpc/", include("osh.hub.osh_xmlrpc.urls")),
]
