from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import TemplateView

admin.autodiscover()


urlpatterns = [
    # Example:
    # (r'^covscanhub/', include('osh.hub.foo.urls')),
    url(r"^$", TemplateView.as_view(template_name="index.html"), name="index"),
    url(r"^$", TemplateView.as_view(template_name="index.html"), name="home/index"),
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # url(r"^$", 'osh.hub.home.views.index_redirect', name="task/list"),
    url(r"^auth/", include("kobo.hub.urls.auth")),
    url(r"^task/", include("osh.hub.scan.task_urls")),
    url(r"^info/arch/", include("kobo.hub.urls.arch")),
    url(r"^info/channel/", include("kobo.hub.urls.channel")),
    url(r"^info/user/", include("kobo.hub.urls.user")),
    url(r"^info/worker/", include("kobo.hub.urls.worker")),
    url(r"^waiving/", include("osh.hub.waiving.urls")),

    url(r"^scan/", include("osh.hub.scan.urls")),

    url(r"^stats/", include("osh.hub.stats.urls")),

    url(r'^admin/', admin.site.urls),

    # Include kobo hub xmlrpc module urls:
    url(r"^xmlrpc/", include("osh.hub.cs_xmlrpc.urls")),
]
