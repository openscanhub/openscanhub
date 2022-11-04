#!/usr/bin/env bash
set -x
source scripts/utils.sh

# Only get container IDs in quiet mode
if [[ $(podman ps -a --filter label=io.podman.compose.project=covscan -q 2>/dev/null | wc -l) -gt 0 ]]; then
    echo "One or more containers are already running under 'podman-compose'. Please use 'podman-compose down' to kill them."
    exit 1
fi

# Remove stale coverage data
rm -rf htmlcov .coverage

# Clone kobo repository if it does not exist
[[ -d kobo ]] || git clone --depth 1 https://github.com/release-engineering/kobo.git
podman pull registry-proxy.engineering.redhat.com/rh-osbs/rhel8-postgresql-12
podman build -f containers/Dockerfile.hub -t osh-hub .
podman build -f containers/Dockerfile.worker -t osh-worker .
podman build -f containers/Dockerfile.client -t osh-client .
podman-compose up -d db osh-hub osh-worker osh-client

while ! podman exec -it osh-hub pg_isready -h db; do sleep 0.5; done
podman exec -it db psql -c 'ALTER USER covscanhub CREATEDB;'

# Wait for hub to be ready before creating users
wait_for_container 'HUB'

podman exec -it osh-hub python3 covscanhub/manage.py shell<<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_user('user', 'user@redhat.com', 'xxxxxx')
User.objects.create_superuser('admin', 'user@redhat.com', 'xxxxxx')
exit()
EOF

# Only generate test coverage report for Covscan(OpenScanHub) project
podman exec -it osh-client env COVSCAN_CONFIG_FILE=covscan/covscan-local.conf PYTHONPATH=.:kobo /usr/bin/coverage-3.6 run --parallel-mode --omit="*site-packages*,*kobo*," covscan/covscan list-mock-configs
podman exec -it osh-client env COVSCAN_CONFIG_FILE=covscan/covscan-local.conf PYTHONPATH=.:kobo /usr/bin/coverage-3.6 run --parallel-mode --omit="*site-packages*,*kobo*," covscan/covscan mock-build --config=fedora-36-x86_64 --brew-build units-2.21-4.fc36

# We have to kill django server and worker to generate coverage files
podman exec -i osh-worker scripts/kill_worker.sh
podman exec -i osh-hub scripts/kill_django_server.sh

# Combine coverage report for hub, worker and client
podman exec -it osh-client /usr/bin/coverage-3.6 combine

# Convert test coverage to html
podman exec -it osh-client /usr/bin/coverage-3.6 html

# Open the coverage report under your favourite browser
echo "Coverage report generated in 'htmlcov' directory."
echo "Use 'xdg-open htmlcov/index.html' command to open it."
