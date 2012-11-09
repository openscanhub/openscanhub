# -*- coding: utf-8 -*-


from covscanhub.other.shortcuts import add_link_field

import django.contrib.admin as admin

from models import Tag, MockConfig, Scan, Package, SystemRelease


@add_link_field('task', 'task', 'hub')
@add_link_field('scan', 'base', field_name='link_base')
@add_link_field('scan', 'parent', field_name='link_parent')
@add_link_field('tag', 'tag', field_name='link_tag')
@add_link_field('package', 'package', field_name='link_package')
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