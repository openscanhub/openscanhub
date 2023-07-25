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
    /usr/bin/coverage-3.6 run --parallel-mode '--omit=*site-packages*,*kobo*,'
    osh/client/osh-cli
)

CLI_XML=(
    env
    OSH_CLIENT_CONFIG_FILE=osh/client/client-local.conf
    PYTHONPATH=.:kobo
    /usr/bin/coverage-3.6 run --parallel-mode '--omit=*site-packages*,*kobo*,'
    osh/hub/scripts/osh-xmlrpc-client.py
)

main() {
    set -ex

    FEDORA_VERSION=37

    ./containers/scripts/init-db.sh --full-dev --minimal "$FORCE"

    # Remove stale coverage data
    rm -rf htmlcov .coverage
    podman exec -it db psql -c 'ALTER USER openscanhub CREATEDB;'

    set -o pipefail
    # Only generate test coverage report for OpenScanHub project
    podman exec -it osh-client "${CLI_COV[@]}" list-analyzers | grep gcc
    podman exec -it osh-client "${CLI_COV[@]}" list-profiles | grep default
    podman exec -it osh-client "${CLI_COV[@]}" list-mock-configs | grep fedora
    podman exec osh-client "${CLI_COV[@]}" mock-build --config=fedora-$FEDORA_VERSION-x86_64 --brew-build units-2.21-5.fc$FEDORA_VERSION | grep http://osh-hub:8000/task/1
    podman exec osh-client "${CLI_COV[@]}" task-info 1 | grep "is_failed = False"
    podman exec -it osh-client "${CLI_COV[@]}" download-results 1
    untar_output=$(tar xvf units*.tar.xz)
    untar_dir_name=$(echo $untar_output | cut -d' ' -f1)
    [[ -f "$untar_dir_name/scan-results.js" ]] && [[ -f "$untar_dir_name/scan-results.html" ]] && [[ -f "$untar_dir_name/scan.log" ]]
    rm -rf units*.tar.xz "$untar_dir_name"

    [[ $(podman exec osh-client "${CLI_COV[@]}" find-tasks -p units) -eq 1 ]]

    podman exec osh-client "${CLI_COV[@]}" diff-build --config=fedora-$FEDORA_VERSION-x86_64 --brew-build units-2.21-5.fc$FEDORA_VERSION | grep http://osh-hub:8000/task/2
    podman exec osh-client "${CLI_COV[@]}" task-info 2 | grep "is_failed = False"
    podman exec -it osh-client "${CLI_COV[@]}" download-results 2
    untar_output=$(tar xvf units*.tar.xz)
    untar_dir_name=$(echo $untar_output | cut -d' ' -f1)
    [[ -f "$untar_dir_name/scan-results.js" ]] && [[ -f "$untar_dir_name/scan-results.html" ]] && [[ -f "$untar_dir_name/scan.log" ]]
    rm -rf units*.tar.xz "$untar_dir_name"

    # `version-diff-build` needs worker to run in background
    podman exec -i osh-worker scripts/kill_worker.sh
    sed -i "s/RUN_TASKS_IN_FOREGROUND = 1/RUN_TASKS_IN_FOREGROUND = 0/g" osh/worker/worker-local.conf
    podman start osh-worker
    podman exec osh-client "${CLI_COV[@]}" version-diff-build --config=fedora-$FEDORA_VERSION-x86_64 --brew-build units-2.21-5.fc$FEDORA_VERSION --base-config=fedora-$FEDORA_VERSION-x86_64 --base-brew-build units-2.21-5.fc$FEDORA_VERSION | grep http://osh-hub:8000/task/3
    podman exec osh-client "${CLI_COV[@]}" task-info 3 | grep "is_failed = False"
    podman exec -it osh-client "${CLI_COV[@]}" download-results 3
    untar_output=$(tar xvf units*.tar.xz)
    untar_dir_name=$(echo $untar_output | cut -d' ' -f1)
    [[ -f "$untar_dir_name/scan-results.js" ]] && [[ -f "$untar_dir_name/scan-results.html" ]] && [[ -f "$untar_dir_name/scan.log" ]]
    rm -rf units*.tar.xz "$untar_dir_name"

    podman exec osh-client "${CLI_XML[@]}" --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx create-scan -b libssh2-1.10.0-5.fc37 -t libssh2-1.10.0-7.fc38 --et-scan-id=1 --release=Fedora-37 --owner=admin --advisory-id=1

    SCAN_STATUS=`podman exec osh-client "${CLI_XML[@]}" --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx get-scan-state 1 2>&1`
    while [[ $SCAN_STATUS == *"QUEUED"* ]] || [[ $SCAN_STATUS == *"SCANNING"* ]]; do
        sleep 10;
        SCAN_STATUS=`podman exec osh-client "${CLI_XML[@]}" --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx get-scan-state 1 2>&1`
    done;

    [[ $SCAN_STATUS == *"PASSED"* ]]

    # priority offset feature testing

    # verify that main task has the right priority
    curl http://localhost:8000/task/5/ | grep -Pzo "<th>Priority</th>\n    <td>20</td>"

    # insert priority offset setting into the database
    podman exec -it db psql -d openscanhub -c "INSERT INTO scan_package (name, blocked, priority_offset) VALUES ('expat', false, 1);"

    # submit errata scan and check its tasks priorities
    podman exec osh-client "${CLI_XML[@]}" --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx create-scan -b expat-2.5.0-1.fc37 -t expat-2.5.0-2.fc38 --et-scan-id=1 --release=Fedora-37 --owner=admin --advisory-id=1

    SCAN_STATUS=`podman exec osh-client "${CLI_XML[@]}" --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx get-scan-state 2 2>&1`
    while [[ $SCAN_STATUS == *"QUEUED"* ]] || [[ $SCAN_STATUS == *"SCANNING"* ]]; do
        sleep 10;
        SCAN_STATUS=`podman exec osh-client "${CLI_XML[@]}" --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx get-scan-state 2 2>&1`
    done;

    [[ $SCAN_STATUS == *"PASSED"* ]]

    # verify that main task has the right priority
    curl http://localhost:8000/task/8/ | grep -Pzo "<th>Priority</th>\n    <td>21</td>"

    # verify subtask priority inheritance if we have recent enough Kobo
    if [ $(git -C kobo log --tags --oneline --grep='0\.26\.0' | wc -l) == 1 ]; then
        curl http://localhost:8000/task/9/ | grep -Pzo "<th>Priority</th>\n    <td>21</td>"
    fi

    podman exec osh-client "${CLI_COV[@]}" mock-build --config=fedora-$FEDORA_VERSION-x86_64 --brew-build expat-2.5.0-1.fc$FEDORA_VERSION | grep http://osh-hub:8000/task/10
    podman exec osh-client "${CLI_COV[@]}" task-info 10 | grep "is_failed = False"

    # verify that mock build task has the right priority
    curl http://localhost:8000/task/10/ | grep -Pzo "<th>Priority</th>\n    <td>11</td>"

    podman exec osh-client "${CLI_COV[@]}" version-diff-build --config=fedora-$FEDORA_VERSION-x86_64 --brew-build expat-2.5.0-1.fc$FEDORA_VERSION --base-config=fedora-$FEDORA_VERSION-x86_64 --base-brew-build expat-2.5.0-1.fc$FEDORA_VERSION | grep http://osh-hub:8000/task/11
    podman exec osh-client "${CLI_COV[@]}" task-info 11 | grep "is_failed = False"
    # verify main tasks priority
    curl http://localhost:8000/task/11/ | grep -Pzo "<th>Priority</th>\n    <td>11</td>"

    # priority offset feature testing end
    podman exec osh-client /usr/bin/coverage-3.6 run --parallel-mode '--omit=*site-packages*,*kobo*,' osh/hub/scripts/osh-xmlrpc-client.py --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx create-scan -b units-2.18-3.fc30 -t units-2.22-5.fc39 --et-scan-id=1 --release=Fedora-37 --owner=admin --advisory-id=1

    # test generation of usage statistics
    podman exec osh-hub /usr/bin/coverage-3.6 run --parallel-mode '--omit=*site-packages*,*kobo*,' osh/hub/scripts/osh-stats

    set +e; set +o pipefail

    # We have to kill django server and worker to generate coverage files
    podman exec -i osh-worker scripts/kill_worker.sh
    podman exec -i osh-hub scripts/kill_django_server.sh

    # Combine coverage report for hub, worker and client
    podman exec -it osh-client /usr/bin/coverage-3.6 combine

    # Avoid generating html reports in GitHub Actions CI
    if [[ "$GITHUB_ACTIONS" = "true" ]];
    then
        # We use codecov in GitHub Actions CI. Upload xml reports to it.
        podman exec -it osh-client /usr/bin/coverage-3.6 xml
    else
        # Convert test coverage to html
        podman exec -it osh-client /usr/bin/coverage-3.6 html
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
