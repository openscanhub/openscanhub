# Deployment of RHEL-8 staging hub

- The following steps should work for a fresh installation as well as
  for replacement of a previously deployed Covscan hub instance.

- install Covscan hub and PostgreSQL database:
```sh
dnf install covscan-hub{,-conf-stage} postgresql-server
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

- update permissions on the `covscanhub` database:
```sh
su - postgres -c 'psql covscanhub'
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA "public" TO "covscanhub";
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA "public" TO "covscanhub";
```

- apply all migrations:
```sh
/usr/lib/python3.6/site-packages/osh/hub/manage.py migrate
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
    - https://covscan.lab.eng.brq2.redhat.com/covscanhub/auth/krb5login/
    - https://covscan.lab.eng.brq2.redhat.com/covscanhub/admin/scan/appsettings/1/change/
    - set value to `N` and save

- enable Covscan stage worker:
    - https://covscan.lab.eng.brq2.redhat.com/covscanhub/admin/hub/worker/add/
    - enter worker key from `/etc/osh/worker.conf` on covscan.lab.eng.brq2.redhat.com
    - set name to `covscan.lab.eng.brq2.redhat.com`
    - pick `noarch` arch and `default` channel
    - set max load to 2 and save

- submit an ET task with:
```sh
osh/hub/scripts/osh-xmlrpc-client.py \
    --hub https://covscan.lab.eng.brq2.redhat.com/covscanhub/xmlrpc/kerbauth/ \
    create-scan -t libidn2-2.3.0-7.el9 --base NEW_PACKAGE --release RHEL-9.0.0 \
    --et-scan-id 1234 --advisory-id 4567 --owner kdudka
```

- check the waiving page: https://covscan.lab.eng.brq2.redhat.com/covscanhub/waiving/

- check the log file: `/var/log/osh/hub/covscanhub.log`

- try to click the `Create Bugzilla` button


# Deployment of RHEL-8 production hub

- similar to deployment of the staging hub instance with a few differences...

- transfer persistent data of covscanhub (takes approx one day to complete):
```sh
ssh root@cov01.lab.eng.brq2.redhat.com \
    tar -C /var/lib -c covscanhub | pv \
    | tar -xvC /var/lib
```

- install the production Covscan hub configuration and postfix:
```sh
dnf install covscan-hub-conf-prod postfix
```

- configure sending of e-mails (rather than disabling it):
```sh
echo 'always_bcc=covscan-auto@redhat.com' >> /etc/postfix/main.cf
systemctl enable --now postfix
```

- transfer TLS certificate and Kerberos keytab from the running instance:
```sh
ssh root@cov01.lab.eng.brq2.redhat.com \
    tar -C /etc/httpd/conf -c cov01.lab.eng.brq2.redhat.com-ssl httpd.keytab \
    | tar -xvC /etc/httpd/conf
```

- transfer UMB client certificate:
```sh
ssh root@cov01.lab.eng.brq2.redhat.com tar -C /etc -c covscanhub | tar -xvC /etc
```

- set `BZ_API_KEY` in `/usr/lib/python3.6/site-packages/osh/hub/settings_local.py`

- make covscanhub logging work:
```sh
dnf install policycoreutils-python-utils
semanage fcontext -a -t httpd_sys_rw_content_t '/var/log/osh/hub(/.*)?'
restorecon -R /var/log/osh/hub
```

- enable redirect to `/covscanhub` by setting `AllowOverride FileInfo`
  in the `/var/www/html` section of `/etc/httpd/conf/httpd.conf` and:
```sh
echo 'RedirectMatch ^/$ /covscanhub' > /var/www/html/.htaccess
systemctl reload httpd
```

- check that e-mail notifications are sent

- check that ET status is updated properly over UMB

# Migration to `osh/hub` name (https://gitlab.cee.redhat.com/covscan/covscan/-/issues/154):

Please follow below steps to handle migration of `covscanhub` to `osh/hub` name:

- Stop `httpd` service.
- Backup below configuration and log files:
    - `/etc/covscanhub/msg-client-covscan.pem`
    - `/usr/lib/python3.6/site-packages/covscanhub/settings_local.py`
    - `/var/log/covscanhub/covscanhub.log`
- Unmount `/var/lib/covscanhub/html`.
- Unmount `/var/lib/covscanhub`.
- Fix mount point entries in `/etc/fstab` to use `/var/lib/osh/hub` path.
- Mount `/var/lib/covscanhub`.
- Mount `/var/lib/covscanhub/html`.
- Update packages through `dnf update`.
- Check if migration to `/usr/lib/python3.6/site-packages/osh/hub/settings_local.py` was handled succesfully.
- Change below paths in `/usr/lib/python3.6/site-packages/osh/hub/settings_local.py`:
```
'filename': '/var/log/osh/hub/hub.log'
FILES_PATH = '/var/lib/osh/hub'
UMB_CLIENT_CERT = '/etc/osh/hub/msg-client-covscan.pem'
```
- Set up SELinux context on the new log directory:
```
semanage fcontext -a -t httpd_sys_rw_content_t '/var/log/osh/hub(/.*)?'
restorecon -R /var/log/osh/hub
```
- Move `/etc/covscanhub/msg-client-covscan.pem` to `/etc/osh/hub/msg-client-covscan.pem`.
- Start `httpd` service.
