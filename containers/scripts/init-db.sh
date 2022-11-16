#!/usr/bin/env bash

# shellcheck disable=1091
source containers/scripts/utils.sh

FULL_DEV=''
FORCE=''
DEPLOY='false'
MINIMAL='true'

main() {
  set -ex

  if [ "$DEPLOY" = true ]; then
    ./containers/scripts/deploy.sh "$FULL_DEV" "$FORCE"
  fi

  if [ "$MINIMAL" = true ]; then
    minimal
  else
    restore
  fi
}

minimal() {
  # weak password used for testing purposes only
  PASSWD=xxxxxx

  # create covscan users
  podman exec -i osh-hub python3 covscanhub/manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
print(User.objects.create_superuser('admin', 'kdudka@redhat.com', '${PASSWD}'))
print(User.objects.create_user('user', 'user@example.com', '${PASSWD}'))
for login in ['idoamara', 'kdudka', 'lbalhar']:
    print(User.objects.create_user(login, 'f{login}@redhat.com', '${PASSWD}'))
EOF

  # dump the database to a file
  podman exec -i db pg_dump -h localhost -U covscanhub \
    | gzip -c > covscanhub-minimal.db.gz

  # print summary on success
  file covscanhub-minimal.db.gz
}

restore() {
  FILEPATH='https://covscan-stage.lab.eng.brq2.redhat.com/covscanhub.db.gz'
  DOWNLOAD=true

  if [ -e covscanhub.db.gz ]; then
    if [ "$(echo "$(curl "${FILEPATH}.SHA512SUM" | cut -d'=' -f2)" covscanhub.db.gz | sha512sum --check)" ]; then
      DOWNLOAD=false
    fi
  fi

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
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --deploy)
      DEPLOY='true'
      shift
      ;;
    --force)
      FORCE='--force'
      shift
      ;;
    --full-dev)
      FULL_DEV='--full-dev'
      shift
      ;;
    --minimal)
      shift
      ;;
    --restore)
      MINIMAL='false'
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
