# -*- coding: utf-8 -*-


from kobo.hub.models import Task, TASK_STATES

from covscanhub.other.shortcuts import add_link_field
from covscanhub.scan.notify import send_scan_notification
from covscanhub.errata.service import rescan

from covscanhub.scan.xmlrpc_helper import finish_scan as h_finish_scan, \
    fail_scan as h_fail_scan, cancel_scan as h_cancel_scan, cancel_scan_tasks

from django.template import RequestContext
from django.conf.urls.defaults import patterns
from django.shortcuts import render_to_response
from django.utils.safestring import mark_safe
from django.contrib import admin

from covscanhub.scan.models import Scan, ScanBinding, SCAN_STATES
from covscanhub.scan.service import extract_logs_from_tarball
from covscanhub.other.admin import register_admin_module

register_admin_module('covscanhub.scan.models', exclude=['Scan'],
                      search_fields=[('Package', ['name']),
                                     ('ScanBinding', ['scan__nvr']),
                                     ('PackageAttribute', ['package__name'], )])
register_admin_module('django.contrib.admin.models')
register_admin_module('south.models')


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
            'entry': scan,
            'opts': self.model._meta,
            'result': mark_safe("Number of e-mails sent: <b>%s</b>" % result),
            'root_path': self.admin_site.root_path,
        }, context_instance=RequestContext(request))

    def fail_scan(self, request, scan_id):
        sb = ScanBinding.objects.get(scan__id=scan_id)
        cancel_scan_tasks(sb.task)
        h_fail_scan(scan_id, "set as failed from admin interface.")
        scan = Scan.objects.get(id=scan_id)

        return render_to_response('admin/scan/scan/state_change.html', {
            'title': 'Fail scan: %s' % scan.nvr,
            'entry': scan,
            'opts': self.model._meta,
            'result': "Scan #%s set to failed" % scan_id,
            'root_path': self.admin_site.root_path,
        }, context_instance=RequestContext(request))

    def finish_scan(self, request, scan_id):
        task = Task.objects.get(scanbinding__scan__id=scan_id)
        task.state = TASK_STATES['CLOSED']
        task.save()
        extract_logs_from_tarball(task.id)
        h_finish_scan(request, scan_id, task.id)
        scan = Scan.objects.get(id=scan_id)

        return render_to_response('admin/scan/scan/state_change.html', {
            'title': 'Finish scan: %s' % scan.nvr,
            'entry': scan,
            'opts': self.model._meta,
            'result': "Scan #%s set to %s" % (
                scan_id,
                SCAN_STATES.get_value(scan.state)
            ),
            'root_path': self.admin_site.root_path,
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
            'entry': scan,
            'opts': self.model._meta,
            'result': result,
            'root_path': self.admin_site.root_path,
        }, context_instance=RequestContext(request))

    def cancel_scan(self, request, scan_id):
        scan = h_cancel_scan(scan_id)
        return render_to_response('admin/scan/scan/state_change.html', {
            'title': 'Cancelation of scan: %s' % scan,
            'entry': scan,
            'opts': self.model._meta,
            'result': "Scan %s cancelled." % (scan),
            'root_path': self.admin_site.root_path,
        }, context_instance=RequestContext(request))

admin.site.register(Scan, ScanAdmin)
