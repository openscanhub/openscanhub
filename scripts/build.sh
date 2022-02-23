#!/bin/bash
# import wait_for_port

. "./scripts/utils.sh" --source-only

RUN=false

main() {
  test_build_env || exit "$?"

  set -e

  # prepare the containers (should be cheap if already prepared)
  (\
    set -x
    podman build -f containers/Dockerfile.worker -t covscanworker .
    podman build -f containers/Dockerfile.hub -t covscanhub .
    podman pull registry-proxy.engineering.redhat.com/rh-osbs/rhel8-postgresql-12
  )

  # HACK: just for safety, use the down command before proceeding
  # up command errors out when the pods are already built
  # this ensures we "restart" them from a known state
  # TODO: find a better way to (re)build env
  podman-compose down
  (set -x; podman-compose up --no-start)

  if [ "$RUN" = true ]; then
    run
  fi
}

run() {
  # start the database and wait until it starts to listen
  (set -x; podman start db)
  wait_for_port 5432

  (set -x; podman start covscanhub)
  wait_for_port 8000
}

#Used for testing the build environment
#
# Returns:
# 0 if everything is setup correctly, 1 there's a version mismatch, 2 if there are missing dependencies and 3 if there's an unknown error
test_build_env() (
  set +e
  # check that we are in the top-level diretory of our git repo
  test -d .git || return 3
  test -f containers/Dockerfile.hub || return 3
  test -f containers/Dockerfile.worker || return 3
  test -f docker-compose.yml || return 3

  # test if podman-compose is installed
  [[ ! $(podman-compose -v) ]] && return 2

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
