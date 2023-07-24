#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

# collect static files from Django itself
osh/hub/manage.py collectstatic --noinput

for _ in $(seq 100); do
    pg_isready -h db && break
    sleep 0.5
done

# Migrations
# If the database is empty or if it has records about already
# applied migrations, this command should work without any troubles.
osh/hub/manage.py migrate

# If the table of mock configs is empty, we most likely have an empty database.
# In this case, we load the initial data into the database to make the OSH
# hub work.
if [ "$(osh/hub/manage.py dumpdata scan.MockConfig)" = "[]" ]; then
    osh/hub/manage.py loaddata \
        osh/hub/{errata,scan}/fixtures/initial_data.json
fi

# Run a dummy SMTP server in background
python3 -m smtpd -n -c DebuggingServer localhost:8025 >> osh/hub/emails.log &

touch /HUB_IS_READY

# Run main web app
coverage-3 run --parallel-mode --omit="*site-packages*,*kobo*," osh/hub/manage.py runserver 0.0.0.0:8000
