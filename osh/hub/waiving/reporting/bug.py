from abc import ABC, abstractmethod

from django.urls import reverse

from osh.hub.other import get_or_none


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
