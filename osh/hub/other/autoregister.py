# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from django.apps import apps
from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html


class OSHModelAdmin(admin.ModelAdmin):
    # common settings
    empty_value_display = '(None)'
    list_per_page = 20
    skipped_apps = ['contenttypes']

    def __init__(self, model, admin_site):
        # fields to show in ChangeList view
        self.list_display = []

        # fields editable directly in ChangeList view
        self.list_editable = []

        # fields to filter through in ChangeList view
        self.list_filter = []

        # fields to search through
        self.search_fields = []

        # better widget for editing of foreign key fields
        # the target ModelAdmin must include the given field in search_fields!
        self.autocomplete_fields = []

        # better widget for editing of m2m fields
        self.filter_horizontal = []

        model_opts = model._meta

        # process all fields
        for field in model_opts.get_fields():
            # primary key
            if field == model_opts.pk:
                self.list_display.insert(0, field.name)
                self.search_fields.append(field.name)
                continue

            # non-relational fields
            if not field.is_relation:
                self.search_fields.append(field.name)
                self.list_display.append(field.name)

                # add useful features to fields with constrained sets of values
                if field.choices or isinstance(field, models.BooleanField):
                    self.list_editable.append(field.name)
                    self.list_filter.append(field.name)

                continue

            # do not process relationship fields pointing to skipped apps
            if field.related_model._meta.app_label in self.skipped_apps:
                self.list_display.append(field.name)
                continue

            # it is not possible to autocomplete auto_created relationship fields
            if not field.auto_created:
                if field.many_to_many:
                    self.filter_horizontal.append(field.name)
                else:
                    self.autocomplete_fields.append(field.name)

            # skip auto_created relationship field pointing to the same model
            if field.auto_created and field.model is field.related_model:
                continue

            # TODO: add support for auto_created ManyToX relationship
            if field.auto_created and not field.one_to_one:
                continue

            if field.many_to_many:
                self.list_display.append(self._generate_changelist_link_func(field))
            else:
                self.list_display.append(self._generate_change_link_func(field))

        super().__init__(model, admin_site)

    def _generate_change_link_func(self, field):
        """
        Return a function that returns a link to a change site of the object
        referenced by given field annotated by its string representation.

        Related docs:
        * https://docs.djangoproject.com/en/dev/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_display
        * https://docs.djangoproject.com/en/dev/ref/contrib/admin/#reversing-admin-urls
        * https://github.com/django/django/blob/921670c6943e9c532137b7d164885f2d3ab436b8/django/db/models/fields/__init__.py#L92-L105
        """
        foreign_model_opts = field.related_model._meta

        # user verbose_name or model name for auto_created fields
        desc = foreign_model_opts.verbose_name if field.auto_created else field.verbose_name

        @admin.display(description=desc)
        def get_link(obj):
            # access the foreign object
            foreign_obj = getattr(obj, field.name)
            if foreign_obj is None:
                return self.empty_value_display

            # obtain admin change url
            view = f'admin:{foreign_model_opts.app_label}_{foreign_model_opts.model_name}_change'
            url = reverse(view, args=[foreign_obj.id])

            return format_html('<a href="{}">{}</a>', url, foreign_obj)

        return get_link

    def _generate_changelist_link_func(self, field):
        """
        Return a function that returns a link to a changelist site with the
        objects referenced by given M2M field annotated by the model name and
        count.

        Related docs:
        * https://docs.djangoproject.com/en/dev/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_display
        * https://docs.djangoproject.com/en/dev/ref/contrib/admin/#reversing-admin-urls
        * https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.ForeignKey.related_query_name
        * https://github.com/django/django/blob/921670c6943e9c532137b7d164885f2d3ab436b8/django/db/models/fields/__init__.py#L92-L105
        """
        foreign_model_opts = field.related_model._meta

        @admin.display(description=foreign_model_opts.verbose_name_plural)
        def get_link(obj):
            # reverse search condition
            search_cond = f'{field.related_query_name()}={obj.pk}'

            # description
            count = getattr(obj, field.name).count()
            description = f'Show related {foreign_model_opts.verbose_name_plural.title()} ({count})'

            # obtain admin changelist url
            view = f'admin:{foreign_model_opts.app_label}_{foreign_model_opts.model_name}_changelist'
            url = reverse(view)

            return format_html('<a href="{}?{}">{}</a>', url, search_cond,
                               description)

        return get_link


def autoregister_app_admin(app, exclude_models=None):
    for model in apps.get_app_config(app).get_models():
        if exclude_models and model in exclude_models:
            continue

        admin_class = type(f'{model.__name__}Admin', (OSHModelAdmin,), dict())
        try:
            admin.site.register(model, admin_class)
        except admin.sites.AlreadyRegistered:
            pass
