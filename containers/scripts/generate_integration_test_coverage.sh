#!/usr/bin/env bash

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
    osh/hub/scripts/covscan-xmlrpc-client.py
)

main() {
    set -ex

    ./containers/scripts/init-db.sh --deploy --full-dev --minimal "$FORCE"

    # Remove stale coverage data
    rm -rf htmlcov .coverage
    podman exec -it db psql -c 'ALTER USER covscanhub CREATEDB;'

    set -o pipefail
    # Only generate test coverage report for Covscan(OpenScanHub) project
    podman exec -it osh-client "${CLI_COV[@]}" list-analyzers | grep gcc
    podman exec -it osh-client "${CLI_COV[@]}" list-profiles | grep default
    podman exec -it osh-client "${CLI_COV[@]}" list-mock-configs | grep fedora
    podman exec osh-client "${CLI_COV[@]}" mock-build --config=fedora-36-x86_64 --brew-build units-2.21-4.fc36 | grep http://osh-hub:8000/task/1
    [[ $(podman exec osh-client "${CLI_COV[@]}" task-info 1 | wc -l) -gt 0 ]]
    podman exec -it osh-client "${CLI_COV[@]}" download-results 1
    untar_output=$(tar xvf units*.tar.xz)
    untar_dir_name=$(echo $untar_output | cut -d' ' -f1)
    [[ -f "$untar_dir_name/scan-results.js" ]] && [[ -f "$untar_dir_name/scan-results.html" ]] && [[ -f "$untar_dir_name/scan.log" ]]
    rm -rf units*.tar.xz "$untar_dir_name"

    [[ $(podman exec osh-client "${CLI_COV[@]}" find-tasks -p units) -eq 1 ]]

    podman exec osh-client "${CLI_COV[@]}" diff-build --config=fedora-36-x86_64 --brew-build units-2.21-4.fc36 | grep http://osh-hub:8000/task/2
    podman exec -it osh-client "${CLI_COV[@]}" download-results 2
    untar_output=$(tar xvf units*.tar.xz)
    untar_dir_name=$(echo $untar_output | cut -d' ' -f1)
    [[ -f "$untar_dir_name/scan-results.js" ]] && [[ -f "$untar_dir_name/scan-results.html" ]] && [[ -f "$untar_dir_name/scan.log" ]]
    rm -rf units*.tar.xz "$untar_dir_name"

    # `version-diff-build` needs worker to run in background
    podman exec -i osh-worker scripts/kill_worker.sh
    sed -i "s/RUN_TASKS_IN_FOREGROUND = 1/RUN_TASKS_IN_FOREGROUND = 0/g" osh/worker/worker-local.conf
    podman start osh-worker
    podman exec osh-client "${CLI_COV[@]}" version-diff-build --config=fedora-36-x86_64 --brew-build units-2.21-4.fc36 --base-config=fedora-36-x86_64 --base-brew-build units-2.21-4.fc36 | grep http://osh-hub:8000/task/3
    podman exec -it osh-client "${CLI_COV[@]}" download-results 3
    untar_output=$(tar xvf units*.tar.xz)
    untar_dir_name=$(echo $untar_output | cut -d' ' -f1)
    [[ -f "$untar_dir_name/scan-results.js" ]] && [[ -f "$untar_dir_name/scan-results.html" ]] && [[ -f "$untar_dir_name/scan.log" ]]
    rm -rf units*.tar.xz "$untar_dir_name"

    podman exec osh-client "${CLI_XML[@]}" --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx create-scan -b mod_security_crs-3.0.0-5.el8 -t mod_security_crs-3.3.0-2.el8 --et-scan-id=1 --release=RHEL-8.5.0 --owner=admin --advisory-id=1

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
    podman exec -it db psql -d covscanhub -c "INSERT INTO scan_package (name, blocked, eligible, priority_offset) VALUES ('expat', false, true, 1);"

    # submit errata scan and check its tasks priorities
    podman exec osh-client "${CLI_XML[@]}" --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx create-scan -b expat-2.2.5-4.el8 -t expat-2.2.5-10.el8_7.1 --et-scan-id=1 --release=RHEL-8.5.0 --owner=admin --advisory-id=1

    SCAN_STATUS=`podman exec osh-client "${CLI_XML[@]}" --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx get-scan-state 2 2>&1`
    while [[ $SCAN_STATUS == *"QUEUED"* ]] || [[ $SCAN_STATUS == *"SCANNING"* ]]; do
        sleep 10;
        SCAN_STATUS=`podman exec osh-client "${CLI_XML[@]}" --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx get-scan-state 2 2>&1`
    done;

    [[ $SCAN_STATUS == *"NEEDS_INSPECTION"* ]]

    # verify that main task has the right priority
    curl http://localhost:8000/task/8/ | grep -Pzo "<th>Priority</th>\n    <td>21</td>"

    # verify subtask priority inheritance if we have recent enough Kobo
    if [ $(git -C kobo log --tags --oneline --grep='0\.26\.0' | wc -l) == 1 ]; then
        curl http://localhost:8000/task/9/ | grep -Pzo "<th>Priority</th>\n    <td>21</td>"
    fi

    podman exec osh-client "${CLI_COV[@]}" mock-build --config=fedora-36-x86_64 --brew-build expat-2.4.9-1.fc36 | grep http://osh-hub:8000/task/10

    # verify that mock build task has the right priority
    curl http://localhost:8000/task/10/ | grep -Pzo "<th>Priority</th>\n    <td>11</td>"

    podman exec osh-client "${CLI_COV[@]}" version-diff-build --config=fedora-36-x86_64 --brew-build expat-2.5.0-1.fc36 --base-config=fedora-36-x86_64 --base-brew-build expat-2.4.9-1.fc36 | grep http://osh-hub:8000/task/11
    # verify main tasks priority
    curl http://localhost:8000/task/11/ | grep -Pzo "<th>Priority</th>\n    <td>11</td>"

    # priority offset feature testing end
    podman exec osh-client /usr/bin/coverage-3.6 run --parallel-mode '--omit=*site-packages*,*kobo*,' osh/hub/scripts/covscan-xmlrpc-client.py --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx create-scan -b python-six-1.3.0-4.el7 -t python-six-1.9.0-2.el7 --et-scan-id=1 --release=RHEL-7.2.0 --owner=admin --advisory-id=1

    set +e; set +o pipefail

    # We have to kill django server and worker to generate coverage files
    podman exec -i osh-worker scripts/kill_worker.sh
    podman exec -i osh-hub scripts/kill_django_server.sh

    # Combine coverage report for hub, worker and client
    podman exec -it osh-client /usr/bin/coverage-3.6 combine

    # Convert test coverage to html
    podman exec -it osh-client /usr/bin/coverage-3.6 html

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
            echo "  -f, --force  Force container rebuild"
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
