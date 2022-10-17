#!/usr/bin/env bash
set -x
ps -ef
# Send kill signal to `coverage` process that forks the actual django development server and wait
# for it to finish
django_server_coverage_pid=$(ps -eo pid,cmd | grep -i runserver | grep -v 'grep' | grep 'coverage' | xargs | cut -d' ' -f1)
kill -15 "$django_server_coverage_pid"
# Wait will print an error if process has been already killed
wait "$django_server_coverage_pid" 2>/dev/null || :
