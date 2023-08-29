#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

set -x
ps -ef
# Send kill signal to `coverage` process that forks the actual django development server and wait
# for it to finish
django_server_coverage_pid=$(ps -eo pid,cmd | grep -i runserver | grep -v 'grep' | grep 'coverage' | xargs | cut -d' ' -f1)
kill -15 "$django_server_coverage_pid"
# Wait will print an error if process has been already killed
wait "$django_server_coverage_pid" 2>/dev/null || :

# Clean up tasks directory in the container. This has to be done here as it may cause issues with
# starting new jobs if the user that runs the job in container is different from host user
rm -rvf osh/hub/tasks
