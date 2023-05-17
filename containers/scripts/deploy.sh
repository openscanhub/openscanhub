#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

# shellcheck disable=1091
source containers/scripts/utils.sh

# podman-compose is currently unable to use profiles
# see: https://github.com/containers/podman-compose/issues/430
CONTAINERS='db osh-hub osh-worker'
if [ "$IS_LINUX" = 1 ]; then
    PROFILE=""
else
    PROFILE="--profile=full-dev"
fi
START='-d'
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

    test_build_env || exit "$?"

    if [ "$START" = '-d' ]; then
        prepare_deploy
    fi

    eval podman-compose -p osh up --build "$START" "$CONTAINERS"

    if [ "$START" = '-d' ]; then
        wait_for_container 'HUB'
        wait_for_db
    fi
}

#Tests the build environment
#
# Returns:
# 0 if everything is setup correctly, 1 there's a version mismatch, 2 if there are missing dependencies and 3 if there's an unknown error
test_build_env() (
    set +e
    # check that we are in the top-level diretory of our git repo
    test -d .git || return 3
    for f in compose.yaml containers/{hub/{Dockerfile,run.sh},{worker,client}.Dockerfile}; do
        test -f "$f" || {
            echo "Missing file: $f"
            return 3
        }
    done

    # test if *-compose is installed
    command -v podman-compose >/dev/null 2>&1
    test $? = 0 || {
        echo 'Missing compose command'
        return 2
    }

    [ "$IS_LINUX" = 0 ] && return 0

    # test podman-compose version
    mapfile -t < <(grep ' version' <(podman-compose -v) |\
        grep -o ' version\s.*' |\
        sed -e 's, version\s*\([[0-9]]*\),\1,')

    # if podman < 3.1.0 then we need podman-compose < 1.x.x
    PODMAN_VER="${MAPFILE[0]}"
    PODMAN_COMPOSE_VER="${MAPFILE[1]}"
    [[ "$(version_compare "$PODMAN_VER" "3.1.0")" = 1 ]] &&\
        [[ "$(version_compare "$PODMAN_COMPOSE_VER" "1.0.0")" = 0 ]] && {
            echo "podman-compose version $PODMAN_COMPOSE_VER is not compatible with podman version $PODMAN_VER"
            return 1
        }

    return 0
)


prepare_deploy() {
    test_deploy_env || exit "$?"

    if [ "$IS_LINUX" = 1 ]; then
        LABEL_PREFIX='io.podman'
    else
        LABEL_PREFIX='com.docker'
    fi

    containers_count="$(podman ps -a --filter label="$LABEL_PREFIX".compose.project=osh --filter status=running -q 2>/dev/null | wc -l)"

    if [[ "$containers_count" -gt 0 ]]; then
        if [ "$FORCE" = true ]; then
            # when running the down command docker won't stop osh-client if not
            # specified causing errors when trying to remove the network
            # we also can't specify container names in down command
            containers=""
            if [ "$IS_LINUX" = 1 ]; then
                containers="db osh-hub osh-worker"
                if [ "$containers_count" -gt 4 ]; then
                    containers+=" osh-client"
                fi
            fi
            podman-compose -p osh $PROFILE down $containers
            return
        else
            # shellcheck disable=2016
            echo 'One or more containers are already running under `compose`. Please use `compose down` to kill them.'
            exit 1
        fi
        # shellcheck disable=2016
        echo 'One or more containers are already running under `compose`. Please use `compose down` to kill them.'
        exit 4
    fi
}


#Tests the deployment environment
#
# Returns:
# 0 if everything is setup correctly, 1 there's a version mismatch, 2 if there
# are missing dependencies and 3 if there's an unknown error
test_deploy_env() (
    set +e
    cd kobo || return 2
    git ls-remote https://github.com/release-engineering/kobo > /dev/null ||\
        git ls-remote https://github.com/frenzymadness/kobo > /dev/null ||\
        return 2
)


clean() {
    set -e

    eval podman-compose "$PROFILE" down -v
    CONTAINERS=$(podman ps -a | grep 'osh' | sed -e "s/[[:space:]]\{2,\}/,/g" | cut -d, -f1)
    echo "$CONTAINERS" | xargs podman rm -f
    IMAGES=$(shell podman images | grep 'osh' | sed -e "s/[[:space:]]\{2,\}/,/g" | cut -d, -f3)
    echo "$IMAGES" | xargs podman rmi -f
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --clean)
            clean
            exit "$?"
            ;;
        --force|-f)
            FORCE='true'
            shift
            ;;
        --full-dev|-F)
            CONTAINERS+=' osh-client'
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
