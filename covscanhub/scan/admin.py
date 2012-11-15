# -*- coding: utf-8 -*-


from covscanhub.other.shortcuts import add_link_field

import django.contrib.admin as admin

from models import Tag, MockConfig, Scan, Package, SystemRelease


@add_link_field('task', 'task', 'hub', field_label="Task")
@add_link_field('scan', 'base', field_name='link_base', field_label="Base")
@add_link_field('scan', 'parent', field_name='link_parent',
                field_label="Parent")
@add_link_field('tag', 'tag', field_name='link_tag', field_label="Tag")
@add_link_field('package', 'package', field_name='link_package',
                field_label="Package")
class ScanAdmin(admin.ModelAdmin):
    list_display = ("id", "nvr", "state", "scan_type", 'link_base',
                    'link_parent', "link_tag",
                    'username', 'link_package', 'link')


class PackageAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "blocked")


admin.site.register(MockConfig)
admin.site.register(Tag)
admin.site.register(SystemRelease)
admin.site.register(Package, PackageAdmin)
admin.site.register(Scan, ScanAdmin)