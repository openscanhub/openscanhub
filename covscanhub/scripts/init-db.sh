#!/usr/bin/env bash

# shellcheck disable=1091
. "./scripts/utils.sh" --source-only

set -e
set -x

# weak password used for testing purposes only
PASSWD=xxxxxx

# start db and covscanhub to apply migrations
./scripts/build.sh --run

(set +e; wait_for_container 'HUB')

# load fixtures
podman exec -i covscanhub python3 covscanhub/manage.py \
    loaddata ./covscanhub/{errata,scan}/fixtures/initial_data.json

# create covscan users
podman exec -i covscanhub python3 covscanhub/manage.py shell << EOF
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
