# -*- coding: utf-8 -*-

from django import forms
from django.db.models import Q

from covscanhub.waiving.models import WAIVER_TYPES


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

    def get_query(self, request):
        self.is_valid()
        search = self.cleaned_data["search"]
        my = self.cleaned_data["my"]
        self.overdue_filled = self.cleaned_data["overdue"]

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

        if my and request.user.is_authenticated():
            query &= Q(owner=request.user)

        return query

    def objects_satisfy(self, q):
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
