#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

# shellcheck disable=1091
source containers/scripts/utils.sh

# podman-compose is currently unable to use profiles
# see: https://github.com/containers/podman-compose/issues/430
CONTAINERS=(
    db
    osh-hub
    osh-worker
)

if [ "$IS_LINUX" = 1 ]; then
    LABEL='io.podman'
    PROFILE=
else
    LABEL='com.docker'
    PROFILE='--profile=full-dev'
fi
LABEL+='.compose.project=osh'
START='-d'
CLEAN='false'
FORCE='false'

help() {
    set +x
    echo "Usage: $0 [--help|-h] [--clean] [--force|-f] [--full-dev|-F] [--no-start]"
    echo
    echo "Options:"
    echo "  --clean          Remove all containers and volumes"
    echo "  -f, --force      Force compose down"
    echo "  -F, --full-dev   Create a system-independent development environment"
    echo "  -h, --help       Show this message"
    echo "  --no-start       Do not start containers"
}

main() {
    set -ex

    test_build_env
    test_deploy_env

    prepare_deploy

    if [ "$CLEAN" = true ]; then
        clean
        exit "$?"
    fi

    podman-compose -p osh up --build $START "${CONTAINERS[@]}"

    if [ "$START" = '-d' ]; then
        wait_for_container 'HUB'
    fi
}

# Tests the build environment
test_build_env() (
    set -e

    test -d .git

    for f in compose.yaml containers/{hub/{Dockerfile,run.sh},{worker,client}.Dockerfile}; do
        test -f "$f"
    done

    # test if *-compose is installed
    command -v podman-compose
)


prepare_deploy() {
    mapfile -t running < <(podman ps $LABEL -q 2>/dev/null)

    if [[ ${#running[@]} -gt 0 ]] && [ "$FORCE" = false ]; then
        # shellcheck disable=2016
        echo 'One or more containers are already running under `compose`. Please use `compose down` to kill them.'
        return 4
    fi

    if [ "$IS_LINUX" != 1 ]; then
        running=()
    fi
    podman-compose -p osh $PROFILE down "${running[@]}"
}


# Tests the deployment environment
test_deploy_env() {
    set -e
    git -C kobo ls-remote https://github.com/release-engineering/kobo > /dev/null
}


clean() {
    mapfile -t containers < <(podman ps -a $LABEL -q 2>/dev/null)
    podman rm -f "${containers[@]}"
    mapfile -t images < <(podman images $LABEL -q 2>/dev/null)
    podman rmi -f "${images[@]}"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --clean)
            CLEAN=true
            shift
            ;;
        --force|-f)
            FORCE='true'
            shift
            ;;
        --full-dev|-F)
            CONTAINERS+=('osh-client')
            shift
            ;;
        --no-start)
            START='--no-start'
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
