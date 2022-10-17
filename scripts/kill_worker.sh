#!/usr/bin/env bash
set -x
ps -ef
# Worker coverage reports are inconsistent due to issues with signal handling
# https://gitlab.cee.redhat.com/covscan/covscan/-/issues/111
covscand_coverage_pid=$(ps -eo pid,cmd | grep -i covscand | grep -v 'grep' | grep 'coverage' | xargs | cut -d' ' -f1)
kill -15 "$covscand_coverage_pid"
# Wait will print an error if process has been already killed
wait "$covscand_coverage_pid" 2>/dev/null || :
