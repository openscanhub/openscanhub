# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

# -*- coding: utf-8 -*-

import datetime
import logging

from django.core.exceptions import ObjectDoesNotExist
from kobo.hub.models import Task

from osh.common.constants import DEFAULT_CHECKER_GROUP
from osh.common.csmock_parser import CsmockAPI, ResultsExtractor
from osh.hub.scan.models import AnalyzerVersion, AppSettings
from osh.hub.service.path import TaskResultPaths
from osh.hub.service.processing import (TaskDiffer, task_has_results,
                                        task_is_diffed)
from osh.hub.waiving.models import (DEFECT_STATES, RESULT_GROUP_STATES,
                                    Checker, CheckerGroup, Defect, Result,
                                    ResultGroup)
from osh.hub.waiving.service import find_processed_in_past

logger = logging.getLogger(__name__)


class TaskResultsProcessor:
    """
    when task finishes, unpack tarballs and make diffs
    """

    def __init__(self, target_task, base_task=None, exclude_dirs=None):
        """
        scan binding to update
        """
        logger.info("Processing tasks '%s' and '%s'", target_task, base_task)
        self.target_task = target_task
        self.target_task_dir = Task.get_task_dir(target_task.id)
        self.target_paths = TaskResultPaths(target_task)
        if base_task:
            self.base_task = base_task
            self.base_paths = TaskResultPaths(base_task)
            self.base_task_dir = Task.get_task_dir(base_task.id)
        self.exclude_dirs = exclude_dirs

    def unpack_results(self):
        tb_path = self.target_paths.get_tarball_path()
        if task_has_results(self.target_task):
            logger.info("Results are already unpacked for task", self.target_task)
            return
        else:
            logger.debug('Unpacking %s', tb_path)
            rex = ResultsExtractor(tb_path, output_dir=self.target_task_dir, unpack_in_temp=False)
            rex.extract_tarball(self.exclude_dirs)

    def generate_diffs(self):
        if self.base_task:
            if task_is_diffed(self.target_task):
                logger.info("Task '%s' is already diffed.", self.target_task)
                return True
            td = TaskDiffer(self.target_task, self.base_task)
            return td.diff_results()


class ScanResultsProcessor:
    """
    when scan finishes, we have to unpack results, do diffs and load
    them to DB; this class is responsible for unpacking and diffing
    """

    def __init__(self, sb, exclude_dirs=None):
        """
        scan binding to update
        """
        logger.info('Processing \'%s\'', sb)
        self.sb = sb
        self.task = sb.task
        self.base_task = None
        if sb.scan.can_have_base():
            self.base_sb = sb.scan.base.scanbinding
            self.base_task = self.base_sb.task
        self.rp = TaskResultsProcessor(self.task, self.base_task, exclude_dirs)

    def unpack_results(self):
        self.rp.unpack_results()

    def generate_diffs(self):
        if self.sb.scan.can_have_base():
            return self.rp.generate_diffs()


class ResultsLoader:
    """
    load results from json to DB and creates waiving.models.Result
    and attaches it to provided sb
    """

    def __init__(self, sb):
        """
        scan binding to update
        """
        self.sb = sb
        self.scan = sb.scan
        self.result = None
        task = Task.objects.get(id=sb.task.id)
        paths = TaskResultPaths(task)
        self.all = CsmockAPI(paths.get_json_results())
        if self.scan.is_errata_scan():
            self.added = CsmockAPI(paths.get_json_added())
            self.fixed = CsmockAPI(paths.get_json_fixed())

    def create_result(self):
        """ create result model """
        self.result = Result()
        self.result.save()  # save for sake of m2m analyzers relation
        analyzers = self.all.get_analyzers()
        if analyzers:
            self.result.set_analyzers(analyzers)
            AnalyzerVersion.objects.update_analyzers_versions(analyzers, self.scan.tag.mock.name)
        scan_metadata = self.all.get_scan_metadata()
        self.result.lines = scan_metadata.get('cov-lines-processed', None)
        time = scan_metadata.get('cov-time-elapsed-analysis', None)
        if time:
            t = datetime.datetime.strptime(time, "%H:%M:%S")
            time_delta = datetime.timedelta(hours=t.hour,
                                            minutes=t.minute,
                                            seconds=t.second)
            self.result.scanning_time = int(time_delta.days * 86400 + time_delta.seconds)
        self.result.save()

        self.sb.result = self.result
        self.sb.save()

    def store_defects(self, defects, defect_state):
        """ put defects in database """
        for defect in defects:
            try:
                key_idx = int(defect['key_event_idx'])
                key_evt = defect['events'][key_idx]
                if key_evt['event'] == 'internal warning':
                    # skip internal warnings
                    continue
            except:  # noqa: B901, E722
                pass
            d = Defect()
            json_checker_name = defect['checker']

            # truncate to fit into the corresponding db field
            json_checker_name = json_checker_name[:64]

            try:
                # get_or_create fails here, because there will be integrity
                # error on group atribute
                checker = Checker.objects.get(name=json_checker_name)
            except ObjectDoesNotExist:
                if json_checker_name.startswith("FB."):
                    # assign numerous FindBugs checkers to FindBugs automatically
                    default_group = "FindBugs"
                else:
                    default_group = DEFAULT_CHECKER_GROUP
                checker = Checker()
                checker.group, _ = CheckerGroup.objects.get_or_create(name=default_group)
                checker.name = json_checker_name
                checker.save()

            rg, created = ResultGroup.objects.get_or_create(
                checker_group=checker.group,
                result=self.result,
                defect_type=defect_state)

            if rg.state == RESULT_GROUP_STATES['UNKNOWN']:
                if defect_state == DEFECT_STATES['NEW']:
                    rg.state = RESULT_GROUP_STATES['NEEDS_INSPECTION']
                elif defect_state == DEFECT_STATES['FIXED']:
                    rg.state = RESULT_GROUP_STATES['INFO']

            rg.defects_count += 1
            rg.save()

            d.checker = checker
            d.result_group = rg
            d.annotation = defect.get('annotation', None)
            d.defect_identifier = defect.get('defect_id', None)
            d.function = defect.get('function', None)

            if d.function:
                # truncate to fit into the corresponding db field
                d.function = str(d.function)[:128]

            d.cwe = defect.get('cwe', None)
            d.result = self.result
            d.state = defect_state
            d.key_event = defect['key_event_idx']
            d.events = defect['events']
            d.save()

    def process(self):
        """ process scan """
        self.create_result()
        if self.scan.is_errata_scan():
            if self.scan.is_newpkg_scan():
                self.store_defects(self.all.get_defects(), DEFECT_STATES['NEW'])
            else:
                self.store_defects(self.fixed.get_defects(), DEFECT_STATES['FIXED'])
                self.store_defects(self.added.get_defects(), DEFECT_STATES['NEW'])

            find_processed_in_past(self.result)

            for rg in ResultGroup.objects.filter(result=self.result):
                counter = 1
                for defect in Defect.objects.filter(result_group=rg):
                    defect.order = counter
                    defect.save()
                    counter += 1


def process_scan(sb):
    exclude_dirs = AppSettings.settings_get_results_tb_exclude_dirs()
    rp = ScanResultsProcessor(sb, exclude_dirs=exclude_dirs)
    rp.unpack_results()
    rp.generate_diffs()
    rl = ResultsLoader(sb)
    rl.process()
