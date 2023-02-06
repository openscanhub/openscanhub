#!/usr/bin/env bash

# collect static files from Django itself
python3.6 covscanhub/manage.py collectstatic --noinput

for _ in $(seq 100); do
    pg_isready -h db && break
    sleep 0.5
done

# Migrations
# If the database is empty or if it has records about already
# applied migrations, this command should work without any troubles.
python3.6 covscanhub/manage.py migrate
ret=$?

# If the pure migration fails, we either have an existing database content
# or the content is not consistent and we need to skip some
# old already-applied migrations. In that case, user is responsible
# for the database and we can ignore issues in migrations.
if [ "$ret" -gt 0 ]; then
    python3.6 covscanhub/manage.py migrate --fake
fi

# If the table of mock configs is empty, we most likely have an empty database.
# In this case, we load the initial data into the database to make the Covscan
# hub work.
if [ "$(python3.6 covscanhub/manage.py dumpdata scan.MockConfig)" = "[]" ]; then
    python3.6 covscanhub/manage.py loaddata \
        covscanhub/{errata,scan}/fixtures/initial_data.json
fi

# Run a dummy SMTP server in background
python3.6 -m smtpd -n -c DebuggingServer localhost:25 >> covscanhub/emails.log &

touch /HUB_IS_READY

# Run main web app
coverage-3.6 run --parallel-mode --omit="*site-packages*,*kobo*," covscanhub/manage.py runserver 0.0.0.0:8000
