#!/bin/bash
set -e
set -x

# check that we are in the top-level diretory of our git repo
test -d .git
test -f containers/Dockerfile.hub
test -f docker-compose.yml

# weak password used for testing purposes only
PASSWD=xxxxxx

# wait until something listens on the specified port
wait_for_port() (
    set +x
    set +e
    port=$1
    cnt=256
    while ((--cnt)); do
        curl -fo/dev/null --no-progress-meter "http://localhost:${port}"
        case $? in
            # we get `curl: (52) Empty reply from server`
            # when we speak HTTP to psql db port
            0|52)
                break
                ;;
            *)
                # wait for the container to become ready
                sleep 1
                ;;
        esac
    done
)

# prepare the containers (should be cheap if already prepared)
podman build -f containers/Dockerfile.hub -t covscanhub .
podman pull docker.io/library/postgres:12
podman-compose up --no-start

# start the database and wait until it starts to listen
podman start db
wait_for_port 5432

# start covscanhub to apply migrations
podman start covscanhub
wait_for_port 8000

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
