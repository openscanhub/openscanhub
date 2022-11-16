#!/usr/bin/env bash

# shellcheck disable=1091
source containers/scripts/utils.sh

# podman-compose is currently unable to use profiles
# see: https://github.com/containers/podman-compose/issues/430
CONTAINERS='db osh-hub osh-worker'
if [[ "$(type podman)" =~ docker ]]; then
  PROFILE="--profile=full-dev"
else
  PROFILE=""
fi
START='--no-start'

main() {
  test_build_env || exit "$?"

  set -ex

  # when running the down command docker won't stop osh-client if not specified
  # causing errors when trying to remove the network
  # we also can't specify container names in down command
  eval podman-compose "$PROFILE" down

  eval podman-compose up --build "$START" "$CONTAINERS"

  if [ "$START" = '-d' ]; then
    wait_for_container 'HUB'
    wait_for_db
  fi
}

#Used for testing the build environment
#
# Returns:
# 0 if everything is setup correctly, 1 there's a version mismatch, 2 if there are missing dependencies and 3 if there's an unknown error
test_build_env() (
  set +e
  # check that we are in the top-level diretory of our git repo
  test -d .git || return 3
  for f in docker-compose.yml containers/{hub/{Dockerfile,run.sh},{worker,client}.Dockerfile}; do
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

  [[ "$(type podman)" =~ docker ]] && return 0

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

clean() {
  podman-compose down -v
  CONTAINERS=$(podman ps -a | grep 'covscan\|osh' | sed -e "s/[[:space:]]\{2,\}/,/g" | cut -d, -f1)
  echo "$CONTAINERS" | xargs podman rm -f
  IMAGES=$(shell podman images | grep 'covscan\|osh' | sed -e "s/[[:space:]]\{2,\}/,/g" | cut -d, -f3)
  echo "$IMAGES" | xargs podman rmi -f
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --full-dev)
      CONTAINERS+=' osh-client'
      shift
      ;;
    --clean)
      clean
      exit "$?"
      ;;
    --run)
      START='-d'
      shift
      ;;
    *)
      echo "Invalid option: $1"
      exit 22 # EINVAL
      ;;
  esac
done

main
