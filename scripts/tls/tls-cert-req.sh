#!/bin/bash -x

KEY_LEN=4096
HOST="cov01.lab.eng.brq.redhat.com"
UPLOAD_URL="https://ca.corp.redhat.com/ca/ee/ca/profileSelect?profileId=caServerCert"

openssl genrsa $KEY_LEN > $HOST.key

openssl req -new -key $HOST.key -out $HOST.csr -config <(cat <<EOF
[req]
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn

[ dn ]
C=US
ST=North Carolina
L=Raleigh
O=Red Hat\, Inc.
OU=Information Technology
CN=$HOST

[ req_ext ]
subjectAltName = @alt_names
 
[ alt_names ]
DNS.1 = $HOST
EOF
)

openssl req -in $HOST.csr -noout -text

(printf "\nGo at %s and upload %s !\n" "$UPLOAD_URL" "$HOST.csr") 2>/dev/null
