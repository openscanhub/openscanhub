#!/bin/sh -ex
su - postgres -c psql <<EOF
    CREATE USER "openscanhub" WITH PASSWORD 'velryba';
    CREATE DATABASE "openscanhub";
    GRANT ALL PRIVILEGES ON DATABASE "openscanhub" TO "openscanhub";
EOF

# wget https://covscan-stage.lab.eng.brq2.redhat.com/openscanhub-limited.db.gz

# gzip -cd openscanhub-limited.db.gz | su - postgres -c 'psql openscanhub'

# rm -f openscanhub-limited.db.gz

su - postgres -c 'psql openscanhub' <<EOF
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA "public" TO "openscanhub";
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA "public" TO "openscanhub";
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
