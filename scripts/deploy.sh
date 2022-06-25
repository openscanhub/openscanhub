#!/usr/bin/env bash

# shellcheck disable=1091
. "./scripts/utils.sh" --source-only

DEBUG=false
INTERACTIVE=''

main() {
  local FILEPATH
  local DOWNLOAD

  test_deploy_env || exit "$?"

  if [[ "$DEBUG" = true ]]; then
    ./covscanhub/scripts/init-db.sh || exit "$?"

    (set -x; podman start osh-worker)

    if [[ "$(type podman)" =~ docker ]]; then
      (set -x; podman run -it "$INTERACTIVE" osh-client bash)
    fi

    return 0
  fi

  ./scripts/build.sh --run

  FILEPATH='https://covscan-stage.lab.eng.brq2.redhat.com/covscanhub.db.gz'
  DOWNLOAD=true

  [ -e covscanhub.db.gz ] &&\
    [ "$(echo "$(curl "${FILEPATH}.SHA512SUM" | cut -d'=' -f2)" covscanhub.db.gz | sha512sum --check)" ] &&\
    DOWNLOAD=false

  if [ "$DOWNLOAD" = true ]; then
    DOWNLOAD_COMMAND='curl -O'
    [ "$({ which aria2c 2>&1; } > /dev/null)" ] && DOWNLOAD_COMMAND='aria2c -s10'
    (set -x; eval "$DOWNLOAD_COMMAND $FILEPATH")
  fi

  (\
    set -x
    gzip -cd covscanhub.db.gz | podman exec -i db psql -h localhost -U osh-hub
    # HACK: this should be turned into a function
    # ref: https://stackoverflow.com/a/16853755/9814181
    podman exec -i osh-hub python3 covscanhub/manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_user('user', 'user@redhat.com', 'xxxxxx')
u = User.objects.get(username='admin')
u.set_password('xxxxxx')
u.save()
EOF
  )
  # TODO: insert worker config

  (set -x; podman start osh-worker)
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
    --no-interactive)
      INTERACTIVE='-d'
      shift
      ;;
    *)
      echo "Invalid option: $1"
      exit 22 # EINVAL
      ;;
  esac
done

main
