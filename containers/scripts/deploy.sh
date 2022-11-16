#!/usr/bin/env bash

# shellcheck disable=1091
source containers/scripts/utils.sh

DEBUG=false

main() {
  test_deploy_env || exit "$?"

  ./containers/scripts/build.sh --run "$FULL_DEV"

  if [[ "$DEBUG" = true ]]; then
    ./containers/scripts/init-db.sh --minimal || exit "$?"
  else
    ./containers/scripts/init-db.sh --restore || exit "$?"
  fi
}

#Used for testing the deployment environment
#
# Returns:
# 0 if everything is setup correctly, 1 there's a version mismatch, 2 if there
# are missing dependencies and 3 if there's an unknown error
test_deploy_env() (
  cd kobo || return 2
  git ls-remote https://github.com/release-engineering/kobo > /dev/null ||\
    git ls-remote https://github.com/frenzymadness/kobo > /dev/null ||\
    return 2
)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --debug)
      DEBUG=true
      shift
      ;;
    --full-dev)
      FULL_DEV='--full-dev'
      shift
      ;;
    *)
      echo "Invalid option: $1"
      exit 22 # EINVAL
      ;;
  esac
done

main
