#!/bin/sh -ex
su - postgres -c psql <<EOF
    CREATE USER "covscanhub" WITH PASSWORD 'velryba';
    CREATE DATABASE "covscanhub";
    GRANT ALL PRIVILEGES ON DATABASE "covscanhub" TO "covscanhub";
EOF

# wget https://covscan-stage.lab.eng.brq2.redhat.com/covscanhub-limited.db.gz

# gzip -cd covscanhub-limited.db.gz | su - postgres -c 'psql covscanhub'

# rm -f covscanhub-limited.db.gz

su - postgres -c 'psql covscanhub' <<EOF
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA "public" TO "covscanhub";
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA "public" TO "covscanhub";
EOF

/usr/lib/python3.6/site-packages/osh/hub/manage.py migrate

python3 /usr/lib/python3.6/site-packages/osh/hub/manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_user('user', 'user@redhat.com', 'xxxxxx')
User.objects.create_superuser('admin', 'user@redhat.com', 'velryba')
EOF

if [ "$(python3 /usr/lib/python3.6/site-packages/osh/hub/manage.py dumpdata scan.MockConfig)" = "[]" ]; then
    python3 /usr/lib/python3.6/site-packages/osh/hub/manage.py loaddata \
    /usr/lib/python3.6/site-packages/osh/hub/{errata,scan}/fixtures/initial_data.json
fi
