#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

set -x
ps -ef
# FIXME: Worker coverage reports are inconsistent due to issues with signal handling
worker_coverage_pid=$(ps -eo pid,cmd | grep -i osh-worker | grep -v 'grep' | grep 'coverage' | xargs | cut -d' ' -f1)
kill -15 "$worker_coverage_pid"
# Wait will print an error if process has been already killed
wait "$worker_coverage_pid" 2>/dev/null || :
