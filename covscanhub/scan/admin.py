# -*- coding: utf-8 -*-


from covscanhub.other.shortcuts import add_link_field

import django.contrib.admin as admin

from models import Tag, MockConfig, Scan, Package, SystemRelease, ScanBinding


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
    list_display = ("id", "tag", "description", "active", "parent_link")

admin.site.register(MockConfig)
admin.site.register(Tag)
admin.site.register(SystemRelease, SystemReleaseAdmin)
admin.site.register(Package, PackageAdmin)
admin.site.register(Scan, ScanAdmin)
admin.site.register(ScanBinding, ScanBindingAdmin)