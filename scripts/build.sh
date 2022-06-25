#!/usr/bin/env bash

# shellcheck disable=1091
. "./scripts/utils.sh" --source-only

RUN=false

main() {
  test_build_env || exit "$?"

  set -e

  # prepare the containers (should be cheap if already prepared)
  (\
    set -x
    podman pull registry-proxy.engineering.redhat.com/rh-osbs/rhel8-postgresql-12
    podman build -f containers/worker.Dockerfile -t osh-worker .
    podman build -f containers/hub/Dockerfile -t osh-hub .
  )
  if [[ ! "$(type podman)" =~ docker ]]; then
    (\
      set -x
      podman build -f containers/client.Dockerfile -t osh-client .
    )
  fi

  # HACK: just for safety, use the down command before proceeding
  # up command errors out when the pods are already built
  # this ensures we "restart" them from a known state
  # TODO: find a better way to (re)build env
  podman-compose down
  if [[ ! "$(type podman)" =~ docker ]]; then
    (set -x; podman-compose --profile full-dev up --no-start)
  else
    (set -x; podman-compose up --no-start db osh-hub osh-worker)
  fi

  if [ "$RUN" = true ]; then
    run
  fi
}

run() {
  set -x
  podman start db osh-hub
}

#Used for testing the build environment
#
# Returns:
# 0 if everything is setup correctly, 1 there's a version mismatch, 2 if there are missing dependencies and 3 if there's an unknown error
test_build_env() (
  set +e
  # check that we are in the top-level diretory of our git repo
  test -d .git || return 3
  test -f containers/hub/Dockerfile || return 3
  test -f containers/hub/run.sh || return 3
  test -f containers/worker.Dockerfile || return 3
  test -f containers/client.Dockerfile || return 3
  test -f docker-compose.yml || return 3

  [[ "$(type podman)" =~ docker ]] && return 0

  # test if podman-compose is installed
  [ ! "$(podman-compose -v)" ] && return 2

  # test its version
  mapfile -t < <(grep ' version' <(podman-compose -v) |\
    grep -o ' version\s.*' |\
    sed -e 's, version\s*\([[0-9]]*\),\1,')

  # if podman < 3.1.0 then we need podman-compose < 1.x.x
  PODMAN_VER="${MAPFILE[0]}"
  PODMAN_COMPOSE_VER="${MAPFILE[1]}"
  [[ "$(version_compare "$PODMAN_VER" "3.1.0")" = 1 ]] &&\
    [[ "$(version_compare "$PODMAN_COMPOSE_VER" "1.0.0")" = 0 ]] && return 1

  return 0
)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run)
      RUN=true
      shift
      ;;
    *)
      echo "Invalid option: $1"
      exit 22 # EINVAL
      ;;
  esac
done

main
