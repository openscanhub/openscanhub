# shellcheck shell=bash
# This script is made to be sourced only

# Exports host's variables to ensure compatibility
export_host_variables() {
    typeset -a tools

    # prefer podman on linux and docker on non-linux platforms
    if [[ "$OSTYPE" =~ 'linux' ]]; then
        tools=(podman docker)
    else
        tools=(docker podman)
    fi

    for tool in "${tools[@]}"; do
        command -v "$tool" || continue

        if [[ "$tool" = podman ]]; then
            export IS_PODMAN=1
        fi

        shopt -s expand_aliases
        # shellcheck disable=2139
        # we want to expand $tool immediately
        alias podman="$tool" && alias podman-compose="$tool-compose"
        return
    done

    echo "podman nor docker were found on this machine!" 1>&2
    exit 1
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
