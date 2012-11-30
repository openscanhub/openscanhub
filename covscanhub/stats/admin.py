# -*- coding: utf-8 -*-


from covscanhub.other.shortcuts import add_link_field

import django.contrib.admin as admin

from models import StatResults, StatType


@add_link_field('stattype', 'stat', field_label="Stat Type")
@add_link_field('systemrelease', 'release', field_label="System Release",
                field_name="release")
class StatResultsAdmin(admin.ModelAdmin):
    list_display = ("id", "link", "value", "date", 'release')


class StatTypeAdmin(admin.ModelAdmin):
    list_display = ("id", 'key', 'short_comment', 'comment', 'group', 'order',
                    'is_release_specific')


admin.site.register(StatType, StatTypeAdmin)
admin.site.register(StatResults, StatResultsAdmin)