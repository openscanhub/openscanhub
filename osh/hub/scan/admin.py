# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import os
from glob import glob

from django.contrib import admin
from django.shortcuts import render
from django.urls import path
from django.utils.safestring import mark_safe
from kobo.hub.models import TASK_STATES, Task

from osh.hub.other.autoregister import OSHModelAdmin, autoregister_app_admin
from osh.hub.scan.models import SCAN_STATES, Scan, ScanBinding
from osh.hub.scan.notify import send_scan_notification
from osh.hub.scan.xmlrpc_helper import cancel_scan as h_cancel_scan
from osh.hub.scan.xmlrpc_helper import cancel_scan_tasks
from osh.hub.scan.xmlrpc_helper import fail_scan as h_fail_scan
from osh.hub.scan.xmlrpc_helper import finish_scan as h_finish_scan


@admin.register(admin.models.LogEntry)
class LogEntryAdmin(OSHModelAdmin):
    """LogEntry ModelAdmin is read only!"""

    def __init__(self, model, admin_site):
        self.readonly_fields = [f.name for f in model._meta.get_fields()]
        super().__init__(model, admin_site)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


autoregister_app_admin('scan', exclude_models=[Scan])


@admin.register(Scan)
class ScanAdmin(OSHModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        slug = '<int:scan_id>/change'
        my_urls = [
            path(f'{slug}/notify/', self.admin_site.admin_view(self.notify)),
            path(f'{slug}/fail/', self.admin_site.admin_view(self.fail_scan)),
            path(f'{slug}/cancel/', self.admin_site.admin_view(self.cancel_scan)),
            path(f'{slug}/finish/', self.admin_site.admin_view(self.finish_scan)),
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
