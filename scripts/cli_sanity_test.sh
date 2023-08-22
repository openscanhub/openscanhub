#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

trap interruption SIGINT
interruption() {
    echo ""
    [ -n "$TEMPOUT" ] &&
        rm -rf "$TEMPOUT"
    echo "Found an interruption. Aborting..."
    # TODO: use an array to store test tasks and abort them all here
    exit
}

# shellcheck disable=SC1091
source containers/scripts/utils.sh

declare -g TEMPOUT

# RETRY=false

test_fixture() {
    export OSH_CLIENT_CONFIG_FILE=osh/client/client-local.conf
    export PYTHONPATH=.:kobo
}

get_task_num() {
    # shellcheck disable=SC2001
    sed -e 's,.*task/\([0-9]*\)/,\1,' <<< "$1"
}

cov-list() (
    set -e
    set -x
    python3 osh/client/osh-cli list-analyzers
    python3 osh/client/osh-cli list-mock-configs
    python3 osh/client/osh-cli list-profiles
    python3 osh/client/osh-cli list-tasks --free --running
    python3 osh/client/osh-cli list-workers
)

cov-mock-build() {
    args="$1"
    config="${2:-fedora-37-$(uname -m)}"
    build="${3:-units-2.21-5.fc37}"

# RETRY=true

    mock-task python3 osh/client/osh-cli mock-build --config="$config"\
                                                    --nvr "$build" "$args"
}

cov-version-diff-build() {
    args="$1"
    config="${2:-fedora-37-$(uname -m)}"
    build="${3:-units-2.21-4.eln116}"
    base_build="${4:-units-2.21-5.fc37}"

# RETRY=true

    mock-task python3 osh/client/osh-cli version-diff-build\
        --base-config="$config" --base-nvr "$base_build"\
        --config="$config" --nvr "$build" "$args"
}

mock-task() {
    cmd="$*"

    grep -q osh-cli <<< "$cmd" || return 1

    echo "+ $cmd --nowait"
    output="$(mktemp)"
    eval "$cmd --nowait" | tee > "$output"
    task_num="$(get_task_num "$(< "$output")")"

    python3 osh/client/osh-cli watch-tasks "$task_num" &
    python3 osh/client/osh-cli watch-log "$task_num" &
    info="$(mktemp)"

    cnt=32
    interval=20
    while ((--cnt)); do
        echo ">> task #$task_num: checking status... (every ${interval}s)"
        python3 osh/client/osh-cli task-info "$task_num" > "$info"

        if grep -qi 'is_finished.*true' "$info"; then
            if grep -qi 'is_failed.*true' "$info"; then
                # TODO: get this path working
                # if [ "$RETRY" = true ]; then
                #   RETRY=false
                #   for i in $(seq 3); do
                #     echo ">> task #$task_num: failed... retrying ($i/3)"
                #     mock-task python3 osh/client/osh-cli resubmit-tasks "$task_num"
                #   done
                # else
                echo ">> task #$task_num: failed..."
                wait
                return 1
                # fi
            fi
            break
        fi

    sleep "$interval"
    done
    if [ "$cnt" = 0 ]; then
        echo ">> task #$task_num: timed out!"
        wait
        return 1
    fi

    echo ">> task #$task_num: finished!"

    echo ">> task #$task_num: fetching results..."
    (set -x; python3 osh/client/osh-cli download-results --dir "$TEMPOUT" "$task_num")

    # is it of any use in this test suite?
    #tar xvf "$TEMPOUT/$build.tar.xz" --dir "task-$task_num"
    # as I cannot think of any use to untar these results for now
    # will just move them so that they don't get overwritten
    mv "$TEMPOUT"/{"$build.tar.xz","task-$task_num.tar.xz"}
    wait
}

main() {
    set -x

    local config
    local build
    TEMPOUT=$(mktemp -dt cli-test-XXXXXX)

    test_fixture
    cov-list ""
    cov-mock-build ""
    cov-version-diff-build ""

    # TODO: test cancel-tasks and find-tasks
}

main
