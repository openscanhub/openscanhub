# -*- coding: utf-8 -*-

from django import forms

from osh.hub.other.exceptions import BrewException
from osh.hub.other.shortcuts import check_brew_build
from osh.hub.scan.models import MockConfig


def validate_brew_build(value):
    try:
        check_brew_build(value)
    except BrewException:
        raise forms.ValidationError('Brew build %s does not exist'
                                    % value)


class ScanSubmissionForm(forms.Form):
    nvr = forms.CharField(validators=[validate_brew_build])
    base = forms.CharField(required=False, help_text="Required only when \
VersionDiffBuild is selected")
    scan_type = forms.ChoiceField(label="Type of scan", choices=(('DiffBuild', 'DiffBuild'), ('MockBuild', 'MockBuild'), ('VersionDiffBuild', 'VersionDiffBuild')))
    mock = forms.ChoiceField(label="Mock profile",
                             choices=((m.name, m.name) for m in
                                      MockConfig.objects.filter(enabled=True)))
    security_checker = forms.BooleanField(label="Security checker",
                                          required=False)
    all_checker = forms.BooleanField(label="All checkers",
                                     required=False)
    comment = forms.CharField(widget=forms.widgets.Textarea())

    def clean(self):
        cleaned_data = super(ScanSubmissionForm, self).clean()
        base = cleaned_data.get("base")
        scan_type = cleaned_data.get("scan_type")

        if not base:
            self._errors['base'] = "Base nvr has to be specified!"
            return cleaned_data
        if scan_type == 'VersionDiffBuild':
            try:
                validate_brew_build(base)
            except forms.ValidationError as e:
                self._errors['base'] = e.messages
        return cleaned_data
