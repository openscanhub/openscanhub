from abc import ABC, abstractmethod

from django.urls import reverse

from osh.hub.other import get_or_none
from osh.hub.waiving.models import WAIVER_TYPES, ResultGroup, Waiver


class AbstractBugReporter(ABC):
    @abstractmethod
    def __init__(self, model, package, release):
        self._model = model
        self.package = package
        self.release = release

    @abstractmethod
    def create_bug(self, request):
        pass

    @abstractmethod
    def update_bug(self, request):
        pass

    def has_bug(self):
        """
        returns True if there is a jira issue created for specified package/release
        """
        return get_or_none(self._model, package=self.package, release=self.release)

    def get_unreported_bugs(self):
        """
        return IS_A_BUG waivers that weren't reported yet
        """
        rgs = ResultGroup.objects.select_related().filter(
            result__scanbinding__scan__package=self.package,
            result__scanbinding__scan__tag__release=self.release,
        )

        valid_ids = []
        for rg in rgs:
            waiver = rg.has_waiver()
            if waiver:
                valid_ids.append(waiver.id)

        waivers = Waiver.waivers.by_package(self.package)\
            .by_release(self.release)\
            .unreported(self._model)\
            .filter(
                state__in=[
                    WAIVER_TYPES['IS_A_BUG'],
                    WAIVER_TYPES['FIX_LATER']
                ],
                id__in=valid_ids
        )
        if waivers:
            return waivers.order_by('date')

    @staticmethod
    def format_waivers(request, waivers):
        """
        return output of waivers/defects that is posted to bugzilla
        """
        comment = '\n'
        for w in waivers:
            group = w.result_group.checker_group.name
            date_time = w.date.strftime('%Y-%m-%d %H:%M:%S %Z'),  # 2013-01-04 04:09:51 EST
            link = request.build_absolute_uri(
                reverse('waiving/waiver',
                        args=(w.result_group.result.scanbinding.id,
                              w.result_group.id))
            )
            comment += (
                f'Group: {group}\n'
                f'Date: {date_time}\n'
                f'Message: {w.message}\n'
                f'Link: {link}\n'
            )
            if w != waivers.reverse()[0]:
                comment += "-" * 78 + "\n\n"
        return comment

    @staticmethod
    def get_checker_groups(waivers):
        return "\n".join(
            name for name in waivers
            .values_list('result_group__checker_group__name', flat=True)
            .distinct()
        )
