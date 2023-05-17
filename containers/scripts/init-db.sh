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
    echo "  -r, --restore   Auto-restore database from backup"
}

main() {
    set -ex

    containers/scripts/deploy.sh "${DEPLOY_ARGS[@]}"

    if [ "$MINIMAL" = true ]; then
        minimal
    elif [ "$RESTORE" = true ]; then
        restore
    else
        help
        exit 1
    fi
}

minimal() {
    set -ex

    # weak password used for testing purposes only
    PASSWD=xxxxxx

    # create OpenScanHub users
    podman exec -i osh-hub python3 osh/hub/manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
print(User.objects.create_superuser('admin', 'kdudka@redhat.com', '${PASSWD}'))
print(User.objects.create_user('user', 'user@example.com', '${PASSWD}'))
for login in ['idoamara', 'kdudka', 'lbalhar']:
    print(User.objects.create_user(login, 'f{login}@redhat.com', '${PASSWD}'))
EOF

    # dump the database to a file
    podman exec -i db pg_dump -h localhost -U openscanhub \
        | gzip -c > openscanhub-minimal.db.gz

    # print summary on success
    file openscanhub-minimal.db.gz
}

restore() {
    FILEPATH='https://covscan-stage.lab.eng.brq2.redhat.com/openscanhub.db.gz'
    DOWNLOAD=true

    if [ -e openscanhub.db.gz ]; then
        if [ "$(echo "$(curl "${FILEPATH}.SHA512SUM" | cut -d'=' -f2)" openscanhub.db.gz | sha512sum --check)" ]; then
            DOWNLOAD=false
        fi
    fi

    if [ "$DOWNLOAD" = true ]; then
        DOWNLOAD_COMMAND='curl -O'
        if [ "$({ which aria2c 2>&1; } > /dev/null)" ]; then
            DOWNLOAD_COMMAND='aria2c -s10'
        fi
        eval "$DOWNLOAD_COMMAND $FILEPATH"
    fi

    gzip -cd openscanhub.db.gz | podman exec -i db psql -h localhost -U openscanhub
    # HACK: this should be turned into a function
    # ref: https://stackoverflow.com/a/16853755/9814181
    podman exec -i osh-hub python3 osh/hub/manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_user('user', 'user@redhat.com', 'xxxxxx')
u = User.objects.get(username='admin')
u.set_password('xxxxxx')
u.save()
EOF
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
