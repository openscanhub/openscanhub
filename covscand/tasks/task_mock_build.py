# -*- coding: utf-8 -*-


from task_diff_build import DiffBuild


class MockBuild(DiffBuild):
    enabled = True

    arches = ["noarch"]    # list of supported architectures
    channels = ["default"] # list of channels
    exclusive = False      # leave False here unless you really know what you're doing
    foreground = False     # if True the task is not forked and runs in the worker process (no matter you run worker without -f)
    priority = 19
    weight = 1.0

    def get_program(self):
        return "cov-mockbuild"
