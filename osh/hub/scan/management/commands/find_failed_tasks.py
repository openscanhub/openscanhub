from datetime import datetime

import requests
from django.core.management.base import BaseCommand
from kobo.hub.models import Task

start_date = datetime(2023, 10, 18)
end_date = datetime(2023, 10, 19, 23, 59, 59)
CSMOCK_VERSION = "csmock-3.5.0.20231018.081735.gf8bfc23.internal-1"


def get_task_log(task_id, log_name="stdout.log"):
    hub = 'https://cov01.lab.eng.brq2.redhat.com/osh'
    url = f"{hub}/task/{task_id}/log/{log_name}"
    response = requests.get(url)
    response.raise_for_status()
    return response.text


class Command(BaseCommand):
    help = 'Find failed jobs affected by OSH-362'

    def filter_failed_tasks_in_between(self, start=start_date, end=end_date):
        return Task.objects.failed().filter(dt_started__range=(start, end))

    def exclude_tasks_with_cspodman_mock_config(self, qs):
        return qs.exclude(args__contains='"mock_config": "cspodman"')

    def exclude_et_tasks(self, qs):
        return qs.exclude(method="ErrataDiffBuild")

    def filter_tasks_by_csmock_version(self, qs, version=CSMOCK_VERSION):
        task_ids = []
        for task in qs:
            if version in get_task_log(task.id):
                task_ids.append(task.id)
        return task_ids

    def handle(self, *args, **options):
        qs = self.filter_failed_tasks_in_between()
        tasks = self.exclude_et_tasks(self.exclude_tasks_with_cspodman_mock_config(qs))
        results = self.filter_tasks_by_csmock_version(tasks)
        self.stdout.write(self.style.SUCCESS(f"Total number of tasks: {len(results)}"))
        for id in results:
            self.stdout.write(self.style.NOTICE(id))
