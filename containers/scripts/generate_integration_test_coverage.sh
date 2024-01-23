#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

# shellcheck disable=1091
source containers/scripts/utils.sh

FORCE=''

CLI_COV=(
    env
    OSH_CLIENT_CONFIG_FILE=osh/client/client-local.conf
    PYTHONPATH=.:kobo
    /usr/bin/coverage-3 run --parallel-mode '--omit=*site-packages*,*kobo*,' --rcfile=/coveragerc
    osh/client/osh-cli
)

CLI_XML=(
    env
    OSH_CLIENT_CONFIG_FILE=osh/client/client-local.conf
    PYTHONPATH=.:kobo
    /usr/bin/coverage-3 run --parallel-mode '--omit=*site-packages*,*kobo*,' --rcfile=/coveragerc
    osh/hub/scripts/osh-xmlrpc-client.py
)

check_results() {
    local task_id="$1" tar_filename untar_dir_name

    tar_filename=$(podman exec -it osh-client "${CLI_COV[@]}" download-results -d~ "$task_id" | grep -oE '[^ ]+\.tar\.xz')
    podman cp "osh-client:/home/osh/$tar_filename" .

    tar xvf "$tar_filename"
    untar_dir_name="${tar_filename%%.*}"
    [[ -f "$untar_dir_name/scan-results.js" ]] && [[ -f "$untar_dir_name/scan-results.html" ]] && [[ -f "$untar_dir_name/scan.log" ]]
    rm -rf "$tar_filename" "$untar_dir_name"
}

main() {
    set -ex

    # Variables setting packages for testing
    FEDORA_VERSION=39
    EXPAT_NVR="expat-2.5.0-3.fc$FEDORA_VERSION"
    LIBSSH2_NVR="libssh2-1.11.0-2.fc$FEDORA_VERSION"
    UNITS_NVR="units-2.22-6.fc$FEDORA_VERSION"

    # Try to run jobs in foreground for better coverage reports
    sed "s/RUN_TASKS_IN_FOREGROUND = 0/RUN_TASKS_IN_FOREGROUND = 1/g" osh/worker/worker-local.conf > osh/worker/worker-local.conf.new
    mv osh/worker/worker-local.conf{.new,}

    ./containers/scripts/init-db.sh --full-dev --minimal "$FORCE"

    # The container may have a different arch than the host!  Moreover, uname -m
    # on macOS on Apple Silicon reports arm64 which is not recognised by Fedora.
    ARCH=$(podman exec osh-client uname -m)

    # Remove stale coverage data
    rm -rf htmlcov .coverage
    podman exec -it osh-client rm -rf '/cov/*'

    set -o pipefail
    # Only generate test coverage report for OpenScanHub project
    podman exec -it osh-client "${CLI_COV[@]}" list-analyzers | grep gcc
    podman exec -it osh-client "${CLI_COV[@]}" list-profiles | grep default
    podman exec -it osh-client "${CLI_COV[@]}" list-mock-configs | grep fedora
    podman exec osh-client "${CLI_COV[@]}" mock-build --profile default --config="fedora-$FEDORA_VERSION-$ARCH" --nvr $UNITS_NVR | grep http://osh-hub:8000/task/1
    podman exec osh-client "${CLI_COV[@]}" task-info 1 | grep "is_failed = False"
    check_results 1

    [[ $(podman exec osh-client "${CLI_COV[@]}" find-tasks -p units) -eq 1 ]]

    podman exec osh-client bash -c "cd /tmp && koji download-build -a src $UNITS_NVR"
    podman exec osh-client "${CLI_COV[@]}" diff-build --config="fedora-$FEDORA_VERSION-$ARCH" /tmp/$UNITS_NVR.src.rpm | grep http://osh-hub:8000/task/2
    podman exec osh-client "${CLI_COV[@]}" task-info 2 | grep "is_failed = False"
    check_results 2

    # `version-diff-build` needs worker to run in background
    sed "s/RUN_TASKS_IN_FOREGROUND = 1/RUN_TASKS_IN_FOREGROUND = 0/g" osh/worker/worker-local.conf > osh/worker/worker-local.conf.new
    mv osh/worker/worker-local.conf{.new,}

    # wait for the worker to restart
    podman restart --time='-1' osh-worker

    podman exec osh-client "${CLI_COV[@]}" version-diff-build --config="fedora-$FEDORA_VERSION-$ARCH" --nvr $UNITS_NVR --base-config="fedora-$FEDORA_VERSION-$ARCH" --base-nvr $UNITS_NVR | grep http://osh-hub:8000/task/3
    podman exec osh-client "${CLI_COV[@]}" task-info 3 | grep "is_failed = False"
    check_results 3

    podman exec osh-client "${CLI_XML[@]}" --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx create-scan -b $LIBSSH2_NVR -t $LIBSSH2_NVR --et-scan-id=1 --release=Fedora-$FEDORA_VERSION --owner=admin --advisory-id=1

    SCAN_STATUS=`podman exec osh-client "${CLI_XML[@]}" --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx get-scan-state 1 2>&1`
    while [[ $SCAN_STATUS == *"QUEUED"* ]] || [[ $SCAN_STATUS == *"SCANNING"* ]]; do
        sleep 10;
        SCAN_STATUS=`podman exec osh-client "${CLI_XML[@]}" --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx get-scan-state 1 2>&1`
    done;

    [[ $SCAN_STATUS == *"PASSED"* ]]

    # priority offset feature testing

    # verify that main task has the right priority
    podman exec osh-client "${CLI_COV[@]}" task-info 5 | grep "priority = 10"

    # insert priority offset setting into the database
    podman exec -it db psql -h localhost -U openscanhub -d openscanhub -c "INSERT INTO scan_package (name, blocked, priority_offset) VALUES ('expat', false, 1);"

    # submit errata scan and check its tasks priorities
    podman exec osh-client "${CLI_XML[@]}" --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx create-scan -b $EXPAT_NVR -t $EXPAT_NVR --et-scan-id=1 --release=Fedora-$FEDORA_VERSION --owner=admin --advisory-id=1

    SCAN_STATUS=`podman exec osh-client "${CLI_XML[@]}" --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx get-scan-state 2 2>&1`
    while [[ $SCAN_STATUS == *"QUEUED"* ]] || [[ $SCAN_STATUS == *"SCANNING"* ]]; do
        sleep 10;
        SCAN_STATUS=`podman exec osh-client "${CLI_XML[@]}" --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx get-scan-state 2 2>&1`
    done;

    [[ $SCAN_STATUS == *"PASSED"* ]]

    # verify that main task has the right priority
    podman exec osh-client "${CLI_COV[@]}" task-info 8 | grep "priority = 11"

    # verify subtask priority inheritance if we have recent enough Kobo
    if [ $(git -C kobo log --tags --oneline --grep='0\.26\.0' | wc -l) == 1 ]; then
        podman exec osh-client "${CLI_COV[@]}" task-info 9 | grep "priority = 11"
    fi

    podman exec osh-client "${CLI_COV[@]}" mock-build --config="fedora-$FEDORA_VERSION-$ARCH" --nvr $EXPAT_NVR | grep http://osh-hub:8000/task/10
    podman exec osh-client "${CLI_COV[@]}" task-info 10 | grep "is_failed = False"

    # verify that mock build task has the right priority
    podman exec osh-client "${CLI_COV[@]}" task-info 10 | grep "priority = 11"

    podman exec osh-client "${CLI_COV[@]}" version-diff-build --config="fedora-$FEDORA_VERSION-$ARCH" --nvr $EXPAT_NVR --base-config="fedora-$FEDORA_VERSION-$ARCH" --base-nvr $EXPAT_NVR | grep http://osh-hub:8000/task/11
    podman exec osh-client "${CLI_COV[@]}" task-info 11 | grep "is_failed = False"
    # verify main tasks priority
    podman exec osh-client "${CLI_COV[@]}" task-info 11 | grep "priority = 11"

    # priority offset feature testing end
    podman exec osh-client "${CLI_XML[@]}" --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx create-scan -b $UNITS_NVR -t $UNITS_NVR --et-scan-id=1 --release=Fedora-$FEDORA_VERSION --owner=admin --advisory-id=1

    # test generation of usage statistics
    podman exec osh-hub /usr/bin/coverage-3 run --parallel-mode '--omit=*site-packages*,*kobo*,' --rcfile=/coveragerc osh/hub/scripts/osh-stats

    set +e; set +o pipefail

    # stop worker to generate coverage files
    podman stop --time='-1' osh-worker

    # restart the hub to generate coverage files
    podman restart --time='-1' osh-hub

    # Combine coverage report for hub, worker and client
    podman exec -it osh-client /usr/bin/coverage-3 combine --rcfile=/coveragerc
    podman cp osh-client:/cov/coverage .

    # Avoid generating html reports in GitHub Actions CI
    if [[ "$GITHUB_ACTIONS" = "true" ]];
    then
        # We use codecov in GitHub Actions CI. Upload xml reports to it.
        podman exec -it osh-client /usr/bin/coverage-3 xml --rcfile=/coveragerc -o /cov/coverage.xml
        podman cp osh-client:/cov/coverage.xml .
    else
        # Convert test coverage to html
        podman exec -it osh-client /usr/bin/coverage-3 html --rcfile=/coveragerc -d /cov/htmlcov
        podman cp osh-client:/cov/htmlcov .
    fi

    # Open the coverage report under your favourite browser
    echo "Coverage report generated in 'htmlcov' directory."
    echo "Use 'xdg-open htmlcov/index.html' command to open it."
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h)
            echo "Usage: $0 [--force|-f]"
            echo
            echo "Options:"
            echo "  -f, --force  Force compose down"
            exit 0
            ;;
        --force)
            FORCE='--force'
            shift
            ;;
        *)
            if [ -z "$1" ]; then
                shift
            else
                echo "Unknown option: $1"
                exit 22 # EINVAL
            fi
            ;;
    esac
done

main
