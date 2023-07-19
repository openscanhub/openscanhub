# shellcheck shell=bash
# This script is made to be sourced only

# Exports host's variables to ensure compatibility
export_host_variables() {
    if [[ "$OSTYPE" =~ 'linux' ]]; then
        export IS_LINUX=1
    else
        export IS_LINUX=0
    fi

    if test "$IS_LINUX" = 0; then
        shopt -s expand_aliases
        alias podman=docker
        alias podman-compose=docker-compose
    fi
}

export_host_variables

# Checks osh container status
#
# @param $1 container name (e.g. hub, worker, client)
#
# Returns:
# 0 if container is running, 1 if it isn't started in 60s
wait_for_container() (
    set +x

    filename="$(echo "$1" | tr '[:lower:]' '[:upper:]')"
    filename+="_IS_READY"

    containername="osh-"
    containername+="$(echo "$1" | tr '[:upper:]' '[:lower:]')"

    count=0
    while ! podman exec -i "$containername" bash -c "[[ -f /$filename ]]"; do
        sleep 1
        count=$((count + 1))
        if test "$count" -gt 60; then
            return 1
        fi
    done
    return 0
)
