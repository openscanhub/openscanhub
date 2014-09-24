# -*- coding: utf-8 -*-
import os
from glob import glob

from kobo.hub.models import Task, TASK_STATES

from covscanhub.other.shortcuts import add_link_field
from covscanhub.scan.notify import send_scan_notification
from covscanhub.errata.service import rescan
from covscanhub.scan.models import Scan, ScanBinding, SCAN_STATES
from covscanhub.other.autoregister import autoregister_admin
from covscanhub.scan.xmlrpc_helper import finish_scan as h_finish_scan, \
    fail_scan as h_fail_scan, cancel_scan as h_cancel_scan, cancel_scan_tasks

from django.template import RequestContext
from django.conf.urls import patterns
from django.shortcuts import render_to_response
from django.utils.safestring import mark_safe
from django.contrib import admin


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
autoregister_admin('south.models')


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
    search_fields = ['package__name', 'nvr',]
    list_per_page = 15
    review_template = 'admin/my_test/myentry/review.html'

    def get_urls(self):
        urls = super(ScanAdmin, self).get_urls()
        my_urls = patterns(
            '',
            (r'(?P<scan_id>\d+)/notify/$',
             self.admin_site.admin_view(self.notify)),
            (r'(?P<scan_id>\d+)/fail/$',
             self.admin_site.admin_view(self.fail_scan)),
            (r'(?P<scan_id>\d+)/cancel/$',
             self.admin_site.admin_view(self.cancel_scan)),
            (r'(?P<scan_id>\d+)/finish/$',
             self.admin_site.admin_view(self.finish_scan)),
            (r'(?P<scan_id>\d+)/rescan/$',
             self.admin_site.admin_view(self.rescan)),
        )
        return my_urls + urls

    def notify(self, request, scan_id):
        result = send_scan_notification(request, scan_id)
        scan = Scan.objects.get(id=scan_id)

        return render_to_response('admin/scan/scan/state_change.html', {
            'title': 'Notify: %s' % scan.nvr,
            'object': scan,
            'opts': self.model._meta,
            'result': mark_safe("Number of e-mails sent: <b>%s</b>" % result),
            'app_label': self.model._meta.app_label,
        }, context_instance=RequestContext(request))

    def fail_scan(self, request, scan_id):
        sb = ScanBinding.objects.get(scan__id=scan_id)
        cancel_scan_tasks(sb.task)
        h_fail_scan(scan_id, "set as failed from admin interface.")
        scan = Scan.objects.get(id=scan_id)

        return render_to_response('admin/scan/scan/state_change.html', {
            'title': 'Fail scan: %s' % scan.nvr,
            'object': scan,
            'opts': self.model._meta,
            'result': "Scan #%s set to failed" % scan_id,
            'app_label': self.model._meta.app_label,
        }, context_instance=RequestContext(request))

    def finish_scan(self, request, scan_id):
        task = Task.objects.get(scanbinding__scan__id=scan_id)
        task.state = TASK_STATES['CLOSED']
        task.save()
        tb_path = glob(os.path.join(Task.get_task_dir(task.id), '*.tar.xz'))[0]
        h_finish_scan(request, scan_id, os.path.basename(tb_path))
        scan = Scan.objects.get(id=scan_id)

        return render_to_response('admin/scan/scan/state_change.html', {
            'title': 'Finish scan: %s' % scan.nvr,
            'object': scan,
            'opts': self.model._meta,
            'result': "Scan #%s set to %s" % (
                scan_id,
                SCAN_STATES.get_value(scan.state)
            ),
            'app_label': self.model._meta.app_label,
        }, context_instance=RequestContext(request))

    def rescan(self, request, scan_id):
        scan = Scan.objects.get(id=scan_id)
        try:
            new_scan = rescan(scan, request.user)
        except Exception, e:
            result = "Unable to rescan: %s" % e
        else:
            result = "New scan #%s submitted." % (new_scan.scan.id)
        return render_to_response('admin/scan/scan/state_change.html', {
            'title': 'Rescan of package: %s' % scan.nvr,
            'object': scan,
            'opts': self.model._meta,
            'result': result,
            'app_label': self.model._meta.app_label,
        }, context_instance=RequestContext(request))

    def cancel_scan(self, request, scan_id):
        scan = h_cancel_scan(scan_id)
        return render_to_response('admin/scan/scan/state_change.html', {
            'title': 'Cancelation of scan: %s' % scan,
            'object': scan,
            'opts': self.model._meta,
            'result': "Scan %s cancelled." % (scan),
            'app_label': self.model._meta.app_label,
        }, context_instance=RequestContext(request))

admin.site.register(Scan, ScanAdmin)
