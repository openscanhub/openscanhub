#!/bin/sh

# Migrations
# If the database is empty or if it has records about already
# applied migrations, this command should work without any troubles.
python3.6 covscanhub/manage.py migrate

# If the pure migration fails, we either have an existing database content
# or the content is not consistent and we need to skip some
# old already-applied migrations. In that case, user is responsible
# for the database and we can ignore issues in migrations.
if [ $? -gt 0 ]; then
  python3.6 covscanhub/manage.py migrate --fake
fi

# Run a dummy SMTP server in background
python3.6 -m smtpd -n -c DebuggingServer localhost:25 >> covscanhub/emails.log &

# Run main web app
python3.6 covscanhub/manage.py runserver 0.0.0.0:8000
