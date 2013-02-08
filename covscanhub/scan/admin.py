# -*- coding: utf-8 -*-


from covscanhub.other.shortcuts import add_link_field
from covscanhub.scan.notify import send_scan_notification

from django.template import RequestContext
from django.conf.urls.defaults import patterns
from django.shortcuts import render_to_response
import django.contrib.admin as admin

from models import Tag, MockConfig, Scan, Package, SystemRelease, ScanBinding


class MockConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "enabled")

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

    review_template = 'admin/my_test/myentry/review.html'

    def get_urls(self):
        urls = super(ScanAdmin, self).get_urls()
        my_urls = patterns('',
            (r'(?P<scan_id>\d+)/notify/$', self.admin_site.admin_view(self.notify)),
        )
        return my_urls + urls

    def notify(self, request, scan_id):
        result = send_scan_notification(request, scan_id)
        scan = Scan.objects.get(id=scan_id)

        return render_to_response('admin/scan/scan/notify.html', {
            'title': 'Notify: %s' % scan.nvr,
            'entry': scan,
            'opts': self.model._meta,
            'result': result,
            'root_path': self.admin_site.root_path,
        }, context_instance=RequestContext(request))


class PackageAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "blocked")


@add_link_field('task', 'task', 'hub', field_name='link_task',
                field_label="Task")
@add_link_field('scan', 'scan', field_name='link_scan', field_label="Scan")
@add_link_field('result', 'result', 'waiving', field_name='link_result',
                field_label="Result")
class ScanBindingAdmin(admin.ModelAdmin):
    list_display = ("id", "link_scan", "link_task", "link_result",)


@add_link_field('systemrelease', 'parent', field_name='parent_link',
                field_label="Parent")
class SystemReleaseAdmin(admin.ModelAdmin):
    list_display = ("id", "tag", "product", "release", "active", "parent_link")


admin.site.register(MockConfig, MockConfigAdmin)
admin.site.register(Tag)
admin.site.register(SystemRelease, SystemReleaseAdmin)
admin.site.register(Package, PackageAdmin)
admin.site.register(Scan, ScanAdmin)
admin.site.register(ScanBinding, ScanBindingAdmin)