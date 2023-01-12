# -*- coding: utf-8 -*-


from __future__ import absolute_import

from .task_mock_build import MockBuild


class DiffBuild(MockBuild):
    enabled = True

    arches = ["noarch"]     # list of supported architectures
    channels = ["default"]  # list of channels
    exclusive = False       # leave False here unless you really know what you're doing
    foreground = False      # if True the task is not forked and runs in the worker process (no matter you run worker without -f)
    priority = 10
    weight = 1.0
