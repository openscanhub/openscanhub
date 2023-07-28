#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

# shellcheck disable=1091
source containers/scripts/utils.sh

DEPLOY_ARGS=()

help() {
    set +x
    echo "Usage: $0 [--help|-h] [--force|-f] [--full-dev|-F] (--minimal|--restore)"
    echo
    echo "Options:"
    echo "  -h, --help      Show this message"
    echo "  -f, --force     Force compose down"
    echo "  -F, --full-dev  Create a system-independent development environment"
    echo "  -m, --minimal   Create a minimal database"
    echo "  --restore       Auto-restore database from backup (DANGEROUS)"
}

main() {
    set -ex

    containers/scripts/deploy.sh "${DEPLOY_ARGS[@]}"

    if [ "$MINIMAL" = true ]; then
        minimal
    elif [ "$RESTORE" = true ]; then
        if [ "$FORCE" = false ]; then
            echo "--restore must be used with --force"
            exit 1
        fi
        restore
    else
        help
        exit 1
    fi
}

minimal() {
    set -ex

    # grant CREATEDB priviledges needed for tests
    podman exec db psql -h localhost -U openscanhub -c 'ALTER USER openscanhub CREATEDB;'

    # create OpenScanHub users
    podman exec osh-hub python3 osh/hub/manage.py loaddata osh/hub/other/test_fixtures/users.json

    # dump the database to a file
    podman exec -i db pg_dump -h localhost -U openscanhub \
        | gzip -c > openscanhub-minimal.db.gz

    # print summary on success
    file openscanhub-minimal.db.gz
}

restore() {
    FQDN='covscan-stage.lab.eng.brq2.redhat.com'

    if ! ping -c1 -W1 "$FQDN"; then
        echo "Please verify that you have access to the internal network"
        exit 1
    fi

    FILENAME='openscanhub-limited.db.gz'

    curl -O "https://${FQDN}/${FILENAME}"

    podman stop osh-hub
    podman exec db dropdb -h localhost -U openscanhub openscanhub
    podman exec db createdb -h localhost -U openscanhub openscanhub
    gzip -cd "$FILENAME" | podman exec -i db psql -h localhost -U openscanhub
    podman start osh-hub

    wait_for_container 'HUB'
    # grant CREATEDB priviledges needed for tests
    podman exec db psql -h localhost -U openscanhub -c 'ALTER USER openscanhub CREATEDB;'

    # create OpenScanHub users
    podman exec osh-hub python3 osh/hub/manage.py loaddata osh/hub/other/test_fixtures/users.json
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --force|-f)
            DEPLOY_ARGS+=('--force')
            shift
            ;;
        --full-dev|-F)
            DEPLOY_ARGS+=('--full-dev')
            shift
            ;;
        --help|-h)
            help
            exit 0
            ;;
        --minimal|-m)
            MINIMAL='true'
            shift
            ;;
        --restore|-r)
            RESTORE='true'
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
