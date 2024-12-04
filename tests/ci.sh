#!/bin/bash

set -exo pipefail

# `TMT_TREE` variable references path that contains clone of git repository to be tested
cd "$TMT_TREE"

# Install test dependencies
dnf install -y openssl postgresql-server /usr/sbin/semanage

# Setup OpenScanHub settings
cp osh/hub/settings_local.ci.py /usr/lib/python3.*/site-packages/osh/hub/settings_local.py
sed "s|http://osh-hub:8000|https://localhost/osh|g" osh/client/client-local.conf > /etc/osh/client.conf

# Setup postgresql
postgresql-setup --initdb
sed -e 's|ident$|md5|' -i /var/lib/pgsql/data/pg_hba.conf
systemctl start postgresql
scripts/setup_db.sh

# csmock user is required to run builds
adduser csmock -G mock

# Configure SELinux
setsebool -P httpd_can_network_connect 1
semanage fcontext -a -t httpd_sys_rw_content_t '/var/log/osh/hub(/.*)?'
restorecon -R /var/log/osh/hub

# Set up self signed certificate before starting httpd
(cd /etc/httpd/conf && openssl req -newkey rsa:4096 -nodes -keyout localhost.key -x509 -sha256 -days 365 -addext "subjectAltName = DNS:localhost, DNS:localhost, DNS:127.0.0.1" -subj "/C=CZ/ST=/L=/O=Red Hat/OU=Plumbers/CN=localhost" -out localhost.crt)
cp /etc/httpd/conf/localhost.crt /etc/pki/ca-trust/source/anchors/ && update-ca-trust

# Set up httpd
touch /var/log/osh/hub/hub.log && chown apache:apache /var/log/osh/hub/hub.log
systemctl start httpd

# Assign native architecture to the worker
python3 scripts/add-worker-arch.py

# Start worker
systemctl start osh-worker

# Enable below lines if firewall is enabled
# firewall-cmd --zone=public --add-port=80/tcp --permanent
# firewall-cmd --zone=public --add-port=443/tcp --permanent
# firewall-cmd --reload

# Variables setting packages for testing
FEDORA_VERSION=41
EXPAT_NVR="expat-2.6.3-1.fc$FEDORA_VERSION"
UNITS_NVR="units-2.23-3.fc$FEDORA_VERSION"

# Test OpenScanHub
/usr/bin/osh-cli mock-build --config=auto --nvr $UNITS_NVR
/usr/bin/osh-cli task-info 1 | grep "is_failed = False"

(cd /tmp && koji download-build -a src $UNITS_NVR)
/usr/bin/osh-cli diff-build --config=fedora-$FEDORA_VERSION-x86_64 /tmp/$UNITS_NVR.src.rpm
/usr/bin/osh-cli task-info 2 | grep "is_failed = False"

osh/hub/scripts/osh-xmlrpc-client.py --hub "https://localhost/osh/xmlrpc/kerbauth/" --username=user --password=xxxxxx create-scan -b $EXPAT_NVR -t $EXPAT_NVR --et-scan-id=1 --release=Fedora-$FEDORA_VERSION --owner=admin --advisory-id=1
SCAN_STATUS=$(osh/hub/scripts/osh-xmlrpc-client.py --hub https://localhost/osh/xmlrpc/kerbauth/ --username=user --password=xxxxxx get-scan-state 1 2>&1)
while [[ $SCAN_STATUS == *"QUEUED"* ]] || [[ $SCAN_STATUS == *"SCANNING"* ]]; do
    sleep 10;
    SCAN_STATUS=$(osh/hub/scripts/osh-xmlrpc-client.py --hub https://localhost/osh/xmlrpc/kerbauth/ --username=user --password=xxxxxx get-scan-state 1 2>&1)
done;
[[ $SCAN_STATUS == *"PASSED"* ]]
