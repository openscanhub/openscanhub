#!/bin/bash -ex
su - postgres -c psql <<EOF
    CREATE USER "openscanhub" WITH PASSWORD 'velryba';
    CREATE DATABASE "openscanhub" WITH OWNER "openscanhub";
EOF

python3 /usr/lib/python3.*/site-packages/osh/hub/manage.py migrate

# create ci users
python3 /usr/lib/python3.*/site-packages/osh/hub/manage.py loaddata osh/hub/other/test_fixtures/users.json

if [ "$(python3 /usr/lib/python3.*/site-packages/osh/hub/manage.py dumpdata scan.MockConfig)" = "[]" ]; then
    python3 /usr/lib/python3.*/site-packages/osh/hub/manage.py loaddata \
        /usr/lib/python3.*/site-packages/osh/hub/{scan,waiving}/fixtures/initial_data.json
fi
