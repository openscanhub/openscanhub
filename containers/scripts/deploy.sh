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

if [ -z "$IS_PODMAN" ]; then
    PROFILE='--profile=full-dev'
fi
LABEL='com.docker.compose.project=osh'
START='-d'
CLEAN='false'
FORCE='false'

help() {
    set +x
    echo "Usage: $0 [--help|-h] [--clean] [--force|-f] [--full-dev|-F] [--no-start]"
    echo
    echo "Options:"
    echo "  --clean          Remove all containers and volumes"
    echo "  -f, --force      Force container rebuild"
    echo "  -F, --full-dev   Create a system-independent development environment"
    echo "  -h, --help       Show this message"
    echo "  --no-start       Do not start containers"
}

main() {
    set -ex

    test_build_env
    test_deploy_env

    if [ "$CLEAN" = true ]; then
        clean
        exit "$?"
    fi

    prepare_deploy
    podman-compose -p osh up --build $START "${CONTAINERS[@]}"

    if [ "$START" = '-d' ]; then
        wait_for_container 'HUB'
    fi
}

# Tests the build environment
test_build_env() (
    test -d .git

    for f in compose.yaml containers/{hub/{Dockerfile,run.sh},{worker,client}.Dockerfile}; do
        test -f "$f"
    done

    # test if *-compose is installed
    command -v podman-compose

    if [[ -n "$IS_PODMAN" ]] && [[ "$OSTYPE" = *darwin* ]] && grep ':[^:]*z$' compose.yaml; then
        echo "podman on macOS does not support SELinux labeling at the moment."
        echo "Please, remove them from compose.yaml and execute this script again."
        exit 1
    fi
)


prepare_deploy() {
    running="$(podman ps --filter label=$LABEL -q)"

    if [[ -n "$running" ]] && [ "$FORCE" = false ]; then
        # shellcheck disable=2016
        echo 'One or more containers are already running under `compose`. Please use `--clean` to kill them.'
        return 4
    fi

    # Bring compose down
    # The $PROFILE variable may be unset.
    # shellcheck disable=2086
    podman-compose -p osh $PROFILE down -v
}


# Tests the deployment environment
test_deploy_env() {
    git -C kobo ls-remote https://github.com/release-engineering/kobo > /dev/null
}


clean() {
    # The $PROFILE variable may be unset.
    # shellcheck disable=2086
    podman-compose -p osh $PROFILE down -v

    images=$(podman images -q 'osh-*' | paste -s -d' ' -)
    # podman images -q has a defined format
    # shellcheck disable=2086
    [ -z "$images" ] || podman rmi -f $images
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
        --help|-h)
            help
            exit
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
