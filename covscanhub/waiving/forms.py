# -*- coding: utf-8 -*-

from django import forms
from django.db.models import Q

from covscanhub.waiving.models import WAIVER_TYPES
from covscanhub.scan.service import get_used_releases


class WaiverForm(forms.Form):
    waiver_type = forms.ChoiceField(
        choices=(
            (w, WAIVER_TYPES.get_item_help_text(w)) for w in WAIVER_TYPES
        )
    )
    message = forms.CharField(widget=forms.widgets.Textarea(),
                              initial="This defect is not a bug because...")


class ScanListSearchForm(forms.Form):
    search = forms.CharField(required=False)
    my = forms.BooleanField(required=False)
    overdue = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(ScanListSearchForm, self).__init__(*args, **kwargs)
        choices = [(item[0], item[1] + '.' + unicode(item[2]))
                   for item in get_used_releases()]
        # first option searches in every release
        choices.insert(0, ('', 'All'))
        self.fields['release'] = forms.ChoiceField(
            choices=choices, label=u'RHEL Release', required=False)
        # The thing is that we want to mark first option as default -- initial
        # FIXME This is actually happening, *somehow*; this doesn't work:
        #   self.initial['release'] = choices[2][0]
        #   self.fields['release'].initial = choices[2][0]
        # It's because BoundField.value()
        # http://stackoverflow.com/questions/657607/setting-the-selected-value-on-a-django-forms-choicefield

    def get_query(self, request):
        if self.is_valid():
            search = self.cleaned_data["search"]
            my = self.cleaned_data["my"]
            self.overdue_filled = self.cleaned_data["overdue"]
            release = self.cleaned_data["release"]
            query = Q()

            if search:
                try:
                    id_query = int(search)
                except ValueError:
                    pass
                else:
                    query |= Q(id=id_query)
                query |= Q(scan__nvr__icontains=search)
                query |= Q(scan__base__nvr__icontains=search)
                query |= Q(scan__username__username__icontains=search)
                query |= Q(scan__tag__release__tag__icontains=search)
            if release:
                query &= Q(scan__tag__release__id=int(release))
            if my and request.user.is_authenticated():
                query &= Q(scan__username=request.user)

            return query
        else:
            return Q()

    def objects_satisfy(self, q):
        """ is run processed correctly on time? """
        if self.overdue_filled:
            # DO NOT USE `if not o.sca...`, because `scan.wai...` may return
            # False and None which are two completely different states:
            #    - False -- scan haven't been processed on time
            #    - None -- scan failed or was cancelled
            return [o.id for o in q if o.scan.waived_on_time() is False]
        else:
            return q

    def extra_query(self):
        return self.overdue_filled
