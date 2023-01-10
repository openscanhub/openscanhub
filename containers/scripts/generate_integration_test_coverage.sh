#!/usr/bin/env bash

# shellcheck disable=1091
source containers/scripts/utils.sh

FORCE=''

CLI_CMD=(
    env
    COVSCAN_CONFIG_FILE=covscan/covscan-local.conf
    PYTHONPATH=.:kobo
    /usr/bin/coverage-3.6 run --parallel-mode '--omit=*site-packages*,*kobo*,'
    covscan/covscan
)

main() {
    set -ex

    ./containers/scripts/init-db.sh --deploy --full-dev --minimal "$FORCE"

    # Remove stale coverage data
    rm -rf htmlcov .coverage
    podman exec -it db psql -c 'ALTER USER covscanhub CREATEDB;'

    set -o pipefail
    # Only generate test coverage report for Covscan(OpenScanHub) project
    podman exec -it osh-client "${CLI_CMD[@]}" list-analyzers | grep gcc
    podman exec -it osh-client "${CLI_CMD[@]}" list-profiles | grep default
    podman exec -it osh-client "${CLI_CMD[@]}" list-mock-configs | grep fedora
    podman exec osh-client "${CLI_CMD[@]}" mock-build --config=fedora-36-x86_64 --brew-build units-2.21-4.fc36 | grep http://osh-hub:8000/task/1
    [[ $(podman exec osh-client "${CLI_CMD[@]}" task-info 1 | wc -l) -gt 0 ]]
    podman exec -it osh-client "${CLI_CMD[@]}" download-results 1
    untar_output=$(tar xvf units*.tar.xz)
    untar_dir_name=$(echo $untar_output | cut -d' ' -f1)
    [[ -f "$untar_dir_name/scan-results.js" ]] && [[ -f "$untar_dir_name/scan-results.html" ]] && [[ -f "$untar_dir_name/scan.log" ]]
    rm -rf units*.tar.xz "$untar_dir_name"

    [[ $(podman exec osh-client "${CLI_CMD[@]}" find-tasks -p units) -eq 1 ]]

    podman exec osh-client "${CLI_CMD[@]}" diff-build --config=fedora-36-x86_64 --brew-build units-2.21-4.fc36 | grep http://osh-hub:8000/task/2
    podman exec -it osh-client "${CLI_CMD[@]}" download-results 2
    untar_output=$(tar xvf units*.tar.xz)
    untar_dir_name=$(echo $untar_output | cut -d' ' -f1)
    [[ -f "$untar_dir_name/scan-results.js" ]] && [[ -f "$untar_dir_name/scan-results.html" ]] && [[ -f "$untar_dir_name/scan.log" ]]
    rm -rf units*.tar.xz "$untar_dir_name"

    # `version-diff-build` needs worker to run in background
    podman exec -i osh-worker scripts/kill_worker.sh
    sed -i "s/RUN_TASKS_IN_FOREGROUND = 1/RUN_TASKS_IN_FOREGROUND = 0/g"  covscand/covscand-local.conf
    podman start osh-worker
    podman exec osh-client "${CLI_CMD[@]}" version-diff-build --config=fedora-36-x86_64 --brew-build units-2.21-4.fc36 --base-config=fedora-36-x86_64 --base-brew-build units-2.21-4.fc36 | grep http://osh-hub:8000/task/3
    podman exec -it osh-client "${CLI_CMD[@]}" download-results 3
    untar_output=$(tar xvf units*.tar.xz)
    untar_dir_name=$(echo $untar_output | cut -d' ' -f1)
    [[ -f "$untar_dir_name/scan-results.js" ]] && [[ -f "$untar_dir_name/scan-results.html" ]] && [[ -f "$untar_dir_name/scan.log" ]]

    podman exec osh-client /usr/bin/coverage-3.6 run --parallel-mode '--omit=*site-packages*,*kobo*,' covscanhub/scripts/covscan-xmlrpc-client.py --hub http://osh-hub:8000/xmlrpc/kerbauth/ --username=user --password=xxxxxx create-scan -b python-six-1.3.0-4.el7 -t python-six-1.9.0-2.el7 --et-scan-id=1 --release=RHEL-7.2.0 --owner=admin --advisory-id=1

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

if [ "$1" = --force ]; then
    FORCE='--force'
fi

main
