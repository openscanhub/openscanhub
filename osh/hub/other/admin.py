# -*- coding: utf-8 -*-

"""
admin.py

Auto-register admin classes with fields and links to linked model classes

based on http://djangosnippets.org/snippets/997/

Sample:

get_group_state = lambda self, instance: \
    GROUP_STATES.get_value(instance.group_state)
defect_states.short_description = 'Group state'

register_admin_module('project.app.models', new_fields={
    'Group': ('group_state_field', get_group_state),
})


"""

from __future__ import absolute_import
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib import admin
from django.db import models as dmodels
from django.db.models import Field, ForeignKey, OneToOneField
from osh.hub.other.decorators import public
from types import ModuleType
import six


def add_link_field(admin_class, field):
    field_name = field.name + '_link'

    def link(self, instance):
        app_name = field.remote_field.parent_model._meta.app_label
        reverse_path = "admin:%s_%s_change" % (
            app_name,
            field.remote_field.parent_model._meta.module_name
        )

        related_instance = getattr(instance, field.name)
        # it might point to None (foreignKey(null=True))
        if related_instance:
            url = reverse(reverse_path, args=(related_instance.id,))
            return mark_safe("<a href='%s'>%s</a>" % (
                url,
                six.text_type(related_instance))
            )
        else:
            return six.text_type(related_instance)
    link.allow_tags = True
    link.short_description = field.name + ' link'
    setattr(admin_class, field_name, link)
    admin_class.readonly_fields = list(
        getattr(admin_class, 'readonly_fields', [])) + [field_name]
    return admin_class, field_name


@public
def register_admin_module(module, exclude=None, new_fields=None,
                          search_fields=None):
    """
    @param module: module containing django.db.models classes
    @type module: str or __module__
        If you are providing str, use absolute path

    @param exclude: list of classes to exclude from auto-register
    @type exclude: iterable of str or None
    @param new_fields: dictionary of additional fields:
        {'model name': ('field_name', callable)}
    @type new_fields: dict or None
    @param search_fields: list of tuples to search in:
        ('model name', ['list', 'of', 'fields'])
    @type search_fields: dict or None
    """
    exclude = exclude or []
    new_fields = new_fields or {}
    search_fields = search_fields or {}
    if isinstance(module, ModuleType):
        models = module
    elif isinstance(module, six.string_types):
        # import module dynamically -- import leaf, not root
        models = __import__(module, fromlist=[module.split('.')[-1]])
    else:
        raise TypeError("invalid type of argument 'module', expected 'str' or \
'ModuleType', got %s." % type(module))

    #get models from current app
    mods = []
    for x in models.__dict__.values():
        if issubclass(type(x), dmodels.base.ModelBase) and \
                getattr(x, '__name__', '') not in exclude:
            mods.append(x)

    admins = []
    #for each model prepare an admin class (Admin<model_name>, model)
    for c in mods:
        admins.append(("%sAdmin" % c.__name__, c))

    #create the admin class and register it
    for (ac, c) in admins:
        admin_class = type(ac, (admin.ModelAdmin,), dict())
        admin_class.list_display = []
        admin_class.list_per_page = 15
        for field in c._meta.fields:
            field_name = field.name
            # create link for relations
            if issubclass(type(field), (ForeignKey, OneToOneField)):
                admin_class, field_name = add_link_field(admin_class, field)
            if issubclass(type(field), (ForeignKey, OneToOneField, Field)):
                admin_class.list_display.append(field_name)

        # add user defined custom fields
        for new_field in six.iterkeys(new_fields):
            if c.__name__ == new_field:
                setattr(admin_class, new_fields[new_field][0],
                        new_fields[new_field][1])
                admin_class.list_display.append(new_fields[new_field][0])

        # add fields to search in
        for model_name, fields_to_search in search_fields:
            if c.__name__ == model_name:
                setattr(admin_class, 'search_fields', fields_to_search)

        try:  # pass gracefully on duplicate registration errors
            admin.site.register(c, admin_class)
        except Exception:
            pass
