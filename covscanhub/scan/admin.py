# -*- coding: utf-8 -*-
import os
from glob import glob

from django import VERSION as django_version
from django.contrib import admin
from django.shortcuts import render
from django.utils.safestring import mark_safe
from kobo.hub.models import TASK_STATES, Task

from covscanhub.errata.service import rescan
from covscanhub.other.autoregister import autoregister_admin
from covscanhub.other.shortcuts import add_link_field
from covscanhub.scan.models import SCAN_STATES, Scan, ScanBinding
from covscanhub.scan.notify import send_scan_notification
from covscanhub.scan.xmlrpc_helper import cancel_scan as h_cancel_scan
from covscanhub.scan.xmlrpc_helper import cancel_scan_tasks
from covscanhub.scan.xmlrpc_helper import fail_scan as h_fail_scan
from covscanhub.scan.xmlrpc_helper import finish_scan as h_finish_scan

# django.conf.urls.url() was deprecated in Django 3.0 and removed in Django 4.0
if django_version[0] >= 3:
    from django.urls import re_path as url
else:
    from django.conf.urls import url

autoregister_admin('covscanhub.scan.models',
                   exclude_models=['Scan'],
                   reversed_relations={'MockConfig': ['analyzers']},
                   admin_fields={
                       'Tag': {'search_fields': ['name', 'mock__name', 'release__tag']},
                       'ScanBinding': {'search_fields': ['scan__nvr', 'scan__package__name']},
                       'Package': {'search_fields': ['name']},
                       'AnalyzerVersion': {'search_fields': ['version', 'analyzer__name', 'mocks__name']},
                   })
autoregister_admin('django.contrib.admin.models')


@add_link_field('scanbinding', 'scanbinding', field_label="Binding",
                field_name="link_bind")
@add_link_field('scan', 'base', field_name='link_base', field_label="Base")
@add_link_field('scan', 'parent', field_name='link_parent',
                field_label="Parent")
@add_link_field('tag', 'tag', field_name='link_tag', field_label="Tag")
@add_link_field('package', 'package', field_name='link_package',
                field_label="Package")
class ScanAdmin(admin.ModelAdmin):
    list_display = ("id", "nvr", "state", "scan_type", 'link_base',
                    'link_parent', "link_tag",
                    'username', 'link_package', 'link_bind', 'enabled')
    raw_id_fields = ("base", "tag", "username", "package", "parent")
    search_fields = ['package__name', 'nvr']
    list_per_page = 15
    review_template = 'admin/my_test/myentry/review.html'

    def get_urls(self):
        urls = super(ScanAdmin, self).get_urls()
        my_urls = [
            url(r'(?P<scan_id>\d+)/notify/$',
                self.admin_site.admin_view(self.notify)),
            url(r'(?P<scan_id>\d+)/fail/$',
                self.admin_site.admin_view(self.fail_scan)),
            url(r'(?P<scan_id>\d+)/cancel/$',
                self.admin_site.admin_view(self.cancel_scan)),
            url(r'(?P<scan_id>\d+)/finish/$',
                self.admin_site.admin_view(self.finish_scan)),
            url(r'(?P<scan_id>\d+)/rescan/$',
                self.admin_site.admin_view(self.rescan)),
        ]
        return my_urls + urls

    def notify(self, request, scan_id):
        result = send_scan_notification(request, scan_id)
        scan = Scan.objects.get(id=scan_id)

        context = {
            'title': 'Notify: %s' % scan.nvr,
            'object': scan,
            'opts': self.model._meta,
            'result': mark_safe("Number of e-mails sent: <b>%s</b>" % result),
            'app_label': self.model._meta.app_label,
        }
        return render(request, 'admin/scan/scan/state_change.html', context)

    def fail_scan(self, request, scan_id):
        sb = ScanBinding.objects.get(scan__id=scan_id)
        cancel_scan_tasks(sb.task)
        h_fail_scan(scan_id, "set as failed from admin interface.")
        scan = Scan.objects.get(id=scan_id)

        context = {
            'title': 'Fail scan: %s' % scan.nvr,
            'object': scan,
            'opts': self.model._meta,
            'result': "Scan #%s set to failed" % scan_id,
            'app_label': self.model._meta.app_label,
        }
        return render(request, 'admin/scan/scan/state_change.html', context)

    def finish_scan(self, request, scan_id):
        task = Task.objects.get(scanbinding__scan__id=scan_id)
        task.state = TASK_STATES['CLOSED']
        task.save()
        tb_path = glob(os.path.join(Task.get_task_dir(task.id), '*.tar.xz'))[0]
        h_finish_scan(request, scan_id, os.path.basename(tb_path))
        scan = Scan.objects.get(id=scan_id)

        context = {
            'title': 'Finish scan: %s' % scan.nvr,
            'object': scan,
            'opts': self.model._meta,
            'result': "Scan #%s set to %s" % (
                scan_id,
                SCAN_STATES.get_value(scan.state)
            ),
            'app_label': self.model._meta.app_label,
        }
        return render(request, 'admin/scan/scan/state_change.html', context)

    def rescan(self, request, scan_id):
        scan = Scan.objects.get(id=scan_id)
        try:
            new_scan = rescan(scan, request.user)
        except Exception as e: # noqa
            result = "Unable to rescan: %s" % e
        else:
            result = "New scan #%s submitted." % (new_scan.scan.id)
        context = {
            'title': 'Rescan of package: %s' % scan.nvr,
            'object': scan,
            'opts': self.model._meta,
            'result': result,
            'app_label': self.model._meta.app_label,
        }
        return render(request, 'admin/scan/scan/state_change.html', context)

    def cancel_scan(self, request, scan_id):
        scan_binding = ScanBinding.objects.by_scan_id(scan_id)
        scan = h_cancel_scan(scan_binding)
        context = {
            'title': 'Cancelation of scan: %s' % scan,
            'object': scan,
            'opts': self.model._meta,
            'result': "Scan %s cancelled." % (scan),
            'app_label': self.model._meta.app_label,
        }
        return render(request, 'admin/scan/scan/state_change.html', context)


admin.site.register(Scan, ScanAdmin)
