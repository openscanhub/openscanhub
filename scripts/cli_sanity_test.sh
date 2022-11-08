#!/usr/bin/env bash

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
. "./scripts/utils.sh" --source-only

declare -g TEMPOUT

DEPLOY=false
FULL_DEV=""
NOWAIT=true
# RETRY=false

test_fixture() {
  export COVSCAN_CONFIG_FILE=covscan/covscan-local.conf
  export PYTHONPATH=.:kobo
}

get_task_num() {
  # shellcheck disable=SC2001
  sed -e 's,.*task/\([0-9]*\)/,\1,' <<< "$1"
}

cov-list() (
  set -e
  set -x
  python3 covscan/covscan list-analyzers
  python3 covscan/covscan list-mock-configs
  python3 covscan/covscan list-profiles
  python3 covscan/covscan list-tasks --free --running
  python3 covscan/covscan list-workers
)

cov-mock-build() {
  args="$1"
  config="${2:-fedora-36-$(uname -m)}"
  build="${3:-units-2.21-4.fc36}"

  # RETRY=true

  mock-task python3 covscan/covscan mock-build --config="$config"\
    --brew-build "$build" "$args"
}

cov-version-diff-build() {
  args="$1"
  config="${2:-fedora-36-$(uname -m)}"
  build="${3:-units-2.21-4.eln116}"
  base_build="${4:-units-2.21-4.fc36}"

  # RETRY=true

  mock-task python3 covscan/covscan version-diff-build\
    --base-config="$config" --base-brew-build "$base_build"\
    --config="$config" --brew-build "$build" "$args"
}

mock-task() {
  cmd="$*"

  grep -q covscan <<< "$cmd" || return 1

  [ "$NOWAIT" = true ] && NOWAIT_STR="--nowait"
  echo "+ $cmd $NOWAIT_STR"
  output="$(mktemp)"
  eval "$cmd $NOWAIT_STR" | tee > "$output"
  task_num="$(get_task_num "$(< "$output")")"

  python3 covscan/covscan watch-tasks "$task_num" &
  python3 covscan/covscan watch-log "$task_num" &
  info="$(mktemp)"

  cnt=32
  interval=20
  while ((--cnt)); do
    echo ">> task #$task_num: checking status... (every ${interval}s)"
    python3 covscan/covscan task-info "$task_num" > "$info"

    if grep -qi 'is_finished.*true' "$info"; then
      if grep -qi 'is_failed.*true' "$info"; then
        # TODO: get this path working
        # if [ "$RETRY" = true ]; then
        #   RETRY=false
        #   for i in $(seq 3); do
        #     echo ">> task #$task_num: failed... retrying ($i/3)"
        #     mock-task python3 covscan/covscan resubmit-tasks "$task_num"
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
  (set -x; python3 covscan/covscan download-results --dir "$TEMPOUT" "$task_num")

  # is it of any use in this test suite?
  #tar xvf "$TEMPOUT/$build.tar.xz" --dir "task-$task_num"
  # as I cannot think of any use to untar these results for now
  # will just move them so that they don't get overwritten
  mv "$TEMPOUT"/{"$build.tar.xz","task-$task_num.tar.xz"}
  wait
}

set_full_dev() {
  FULL_DEV="--full-dev"
}

main() {
  set -x

  local config
  local build
  TEMPOUT=$(mktemp -dt cli-test-XXXXXX)

  if [[ "$(type podman)" =~ docker ]]; then
    set_full_dev
  fi

  if [ "$DEPLOY" = true ]; then
    ./containers/scripts/deploy.sh --debug "$FULL_DEV" --no-interactive || exit "$?"
  fi

  if [[ -z "$FULL_DEV" ]]; then
    podman start osh-client
  else
    test_fixture
    cov-list ""
    cov-mock-build ""
    cov-version-diff-build ""
  fi

  # TODO: test cancel-tasks and find-tasks
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --deploy)
      DEPLOY=true
      shift
      ;;
    --full-dev)
      set_full_dev
      shift
      ;;
    *)
      echo "Invalid option: $1"
      exit 22 # EINVAL
      ;;
  esac
done

main
