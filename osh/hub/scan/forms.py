# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

from django import forms
from django.db.models import Q

from osh.hub.errata.check import check_build, check_nvr
from osh.hub.scan.models import MockConfig, Package, PackageAttribute


class PackageSearchForm(forms.Form):
    blocked = forms.BooleanField(required=False)
    search = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.order_by = kwargs.pop('order_by', ['name'])
        super().__init__(*args, **kwargs)

    def get_query(self, request):
        self.is_valid()
        blocked = self.cleaned_data["blocked"]
        search = self.cleaned_data["search"]

        query = Q()
        if search:
            query &= Q(name__icontains=search)

        if blocked:
            query &= Q(blocked=True) | Q(id__in=PackageAttribute.objects.get_blocked_packages())

        return Package.objects.filter(query).order_by(*self.order_by)


def validate_brew_build(value):
    try:
        check_nvr(value)
        check_build(value)
    except RuntimeError as e:
        raise forms.ValidationError(e)


class ScanSubmissionForm(forms.Form):
    nvr = forms.CharField(validators=[validate_brew_build])
    base = forms.CharField(required=False, help_text="Required only when \
VersionDiffBuild is selected")
    scan_type = forms.ChoiceField(label="Type of scan", choices=(('DiffBuild', 'DiffBuild'), ('MockBuild', 'MockBuild'), ('VersionDiffBuild', 'VersionDiffBuild')))
    mock = forms.ChoiceField(label="Mock profile")
    comment = forms.CharField(required=False, widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # dynamic fields must be initialized in the __init__ method
        self.fields['mock'].choices = ((m.name, m.name) for m in
                                       MockConfig.objects.filter(enabled=True))

    def clean(self):
        cleaned_data = super().clean()
        base = cleaned_data.get("base")
        scan_type = cleaned_data.get("scan_type")

        if scan_type == 'VersionDiffBuild':
            if not base:
                self.add_error('base', "Base nvr has to be specified!")
                return cleaned_data
            try:
                validate_brew_build(base)
            except forms.ValidationError as e:
                self.add_error('base', e.messages)
        return cleaned_data
