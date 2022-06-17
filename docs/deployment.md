# Deployment of RHEL-8 staging hub

- The following steps should work for a fresh installation as well as
  for replacement of a previously deployed Covscan hub instance.

- install Covscan hub:
```sh
dnf install covscan-hub{,-conf-stage}
```

- prepare PostgreSQL database server:
```sh
systemctl stop httpd postgresql
mv -fvT --backup=numbered /var/lib/pgsql/data/ /root/pgsql-data
postgresql-setup --initdb
sed -e 's|ident$|md5|' -i /var/lib/pgsql/data/pg_hba.conf
systemctl enable --now postgresql
```

- create `covscanhub` database:
```sh
su - postgres -c psql
    CREATE USER "covscanhub" WITH PASSWORD 'velryba';
    CREATE DATABASE "covscanhub";
    GRANT ALL PRIVILEGES ON DATABASE "covscanhub" TO "covscanhub";
```

- import data from production Covscan:
```sh
gzip -cd covscandb.sql.gz | su - postgres -c 'psql covscanhub'
```

- execute conversion SQL script:
```sh
su - postgres -c 'psql covscanhub' < production_to_dev_database.sql
```

- update permissions on the `covscanhub` database:
```sh
su - postgres -c 'psql covscanhub'
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA "public" TO "covscanhub";
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA "public" TO "covscanhub";
```

- mark all migrations as applied:
```sh
python3.6 /usr/lib/python3.6/site-packages/covscanhub/manage.py migrate --fake
python3.6 /usr/lib/python3.6/site-packages/covscanhub/manage.py migrate
```

- start web server:
```sh
setsebool -P httpd_can_network_connect 1
systemctl enable --now httpd
firewall-cmd --zone=public --add-port=80/tcp --permanent
firewall-cmd --zone=public --add-port=443/tcp --permanent
firewall-cmd --reload
```

- disable sending of e-mails:
    - https://covscan.lab.eng.brq.redhat.com/covscanhub/auth/krb5login/
    - https://covscan.lab.eng.brq.redhat.com/covscanhub/admin/scan/appsettings/1/change/
    - set value to `N` and save

- enable Covscan stage worker:
    - https://covscan.lab.eng.brq.redhat.com/covscanhub/admin/hub/worker/add/
    - enter worker key from `/etc/covscan/covscand.conf` on covscan.lab.eng.brq.redhat.com
    - set name to `covscan.lab.eng.brq.redhat.com`
    - pick `noarch` arch and `default` channel
    - set max load to 2 and save

- submit an ET task with:
```sh
covscanhub/scripts/covscan-xmlrpc-client.py \
    --hub https://covscan.lab.eng.brq.redhat.com/covscanhub/xmlrpc/kerbauth/ \
    create-scan -t libidn2-2.3.0-7.el9 --base NEW_PACKAGE --release RHEL-9.0.0 \
    --et-scan-id 1234 --advisory-id 4567 --owner kdudka
```

- check the waiving page: https://covscan.lab.eng.brq.redhat.com/covscanhub/waiving/

- check the log file: `/var/log/covscanhub/covscanhub.log`
