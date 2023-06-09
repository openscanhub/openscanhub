#!/bin/bash -x
dnf remove -y $(rpm -qa | grep -i "covscan\|osh")
dnf install --refresh -y python3-pip git
git clone $PACKIT_SOURCE_URL
git checkout $PACKIT_SOURCE_BRANCH
cd openscanhub
python3 -m pip install setuptools
# We are making lots of tweaks in configurations while setting up this job, which may cause
# issues with SELinux. Keep SELinux in permissive mode and fix any SELinux warnings before
# enabling it in future.
setenforce 0
systemctl status
dnf install -y findutils git make openssl python36 python3-dnf-plugins-core python3-setuptools rpm-build postgresql-server koji
dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
dnf install -y --allowerasing osh-client osh-common osh-hub osh-hub-conf-devel osh-worker osh-worker-conf-devel
# dnf install -y --allowerasing $(ls epel-8-x86_64/*.rpm | grep -v "stage\|prod\|src")
systemctl stop httpd postgresql
# setup openscanhub settings
cp osh/hub/settings_local.ci.py /usr/lib/python3.6/site-packages/osh/hub/settings_local.py
# setup postgresql
mv -fvT --backup=numbered /var/lib/pgsql/data/ /root/pgsql-data
postgresql-setup --initdb
sed -e 's|ident$|md5|' -i /var/lib/pgsql/data/pg_hba.conf
systemctl start postgresql
scripts/setup_db.sh
# csmock user is required to run builds
adduser csmock -G mock || true
# Enable below line if SELinux is in restrictive mode
# setsebool -P httpd_can_network_connect 1
# Set up self signed certificate before starting httpd
(cd /etc/httpd/conf && openssl req -newkey rsa:4096 -nodes -keyout localhost.key -x509 -sha256 -days 365 -addext "subjectAltName = DNS:localhost, DNS:localhost, DNS:127.0.0.1" -subj "/C=CZ/ST=/L=/O=Red Hat/OU=Plumbers/CN=localhost" -out localhost.crt)
cp /etc/httpd/conf/localhost.crt /etc/pki/ca-trust/source/anchors/ && update-ca-trust
cp osh/hub/osh-hub-httpd.conf /etc/httpd/conf.d/osh-hub-httpd.conf
# Handle migration from `covscanhub-httpd.conf` to `osh-hub-httpd.conf`
# Remove stale `/etc/httpd/conf.d/covscanhub-httpd.conf` file if it exists
# https://gitlab.cee.redhat.com/covscan/covscan/-/merge_requests/216
rm -f /etc/httpd/conf.d/covscanhub-httpd.conf
touch /var/log/osh/hub/hub.log && chown apache:apache /var/log/osh/hub/hub.log
systemctl start httpd osh-worker
# Enable below lines if firewall is enabled
firewall-cmd --zone=public --add-port=80/tcp --permanent
firewall-cmd --zone=public --add-port=443/tcp --permanent
firewall-cmd --reload
sed -i "s|http://osh-hub:8000|https://localhost/osh|g" osh/client/client-local.conf
OSH_CLIENT_CONFIG_FILE=osh/client/client-local.conf /usr/bin/osh-cli mock-build --config=fedora-37-x86_64 --brew-build units-2.21-5.fc37 --nowait
sleep 60
tail /var/log/osh/worker.log /var/log/osh/hub/hub.log
OSH_CLIENT_CONFIG_FILE=osh/client/client-local.conf /usr/bin/osh-cli task-info 1 | grep "is_failed = False"
osh/hub/scripts/osh-xmlrpc-client.py --hub "https://localhost/osh/xmlrpc/kerbauth/" --username=user --password=xxxxxx create-scan -b expat-2.5.0-1.fc37 -t expat-2.5.0-2.fc38 --et-scan-id=1 --release=Fedora-37 --owner=admin --advisory-id=1
