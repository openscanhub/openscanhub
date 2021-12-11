#!/bin/sh

# Apply all the migrations
python3.6 covscanhub/manage.py migrate

# Run a dummy SMTP server in background
python3.6 -m smtpd -n -c DebuggingServer localhost:25 >> covscanhub/emails.log &

# Run main web app
python3.6 covscanhub/manage.py runserver 0.0.0.0:8000
