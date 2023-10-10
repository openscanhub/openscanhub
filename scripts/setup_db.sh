#!/bin/sh -ex
su - postgres -c psql <<EOF
    CREATE USER "openscanhub" WITH PASSWORD 'velryba';
    CREATE DATABASE "openscanhub" WITH OWNER "openscanhub";
EOF

python3 /usr/lib/python3.*/site-packages/osh/hub/manage.py migrate

python3 /usr/lib/python3.*/site-packages/osh/hub/manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_user('user', 'user@redhat.com', 'xxxxxx')
User.objects.create_superuser('admin', 'user@redhat.com', 'velryba')
EOF

if [ "$(python3 /usr/lib/python3.*/site-packages/osh/hub/manage.py dumpdata scan.MockConfig)" = "[]" ]; then
    python3 /usr/lib/python3.*/site-packages/osh/hub/manage.py loaddata \
        /usr/lib/python3.*/site-packages/osh/hub/{errata,scan}/fixtures/initial_data.json
fi
