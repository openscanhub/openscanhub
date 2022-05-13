# UMB (Unified Message Bus)


## Requesting access to UMB
- instructions:
    - https://source.redhat.com/groups/public/enterprise-services-platform/it_platform_wiki/umb_client_guide
    - https://source.redhat.com/groups/public/identity-access-management/identity__access_management_wiki/ldap_service_accounts__certificates_for_accessing_shared_services

- client certificates
    - stage: https://ca.corp.redhat.com:8443/ca/ee/ca/displayBySerial?serialNumber=268306926
    - prod:  https://ca.corp.redhat.com:8443/ca/ee/ca/displayBySerial?serialNumber=268306930

- tickets requesting access to UMB:
    - RITM1174540 - LDAP service accounts
    - RITM1177833 - UMB access request

- obtaining a client certificate in file:
    $ git clone https://gitlab.corp.redhat.com/it-iam/utility.git
    $ cd utility/PKI
    $ ./get_rhcs_app_cert.sh covscan nonprod
    [...]

    $ { openssl x509 -in nonprod-covscan.crt && openssl rsa -in nonprod-covscan.key;} > nonprod-umb-covscan.pem

    $ ./get_rhcs_app_cert.sh covscan prod
    [...]

    $ { openssl x509 -in covscan.crt && openssl rsa -in covscan.key;} > umb-covscan.pem

## Debug UMB
```
PN_TRACE_DRV=true ./covscanhub/scripts/umb-emit.py
```

## Watch messages on staging UMB
- using web browser:
    - https://datagrepper.stage.engineering.redhat.com/raw/?category=covscan


## Make it work with SELinux
```
# setsebool -P httpd_can_network_connect 1
```

- otherwise /var/log/audit/audit.log will contain errors like this on UMB send:
```
type=AVC msg=audit(1575904903.583:1229): avc:  denied  { name_connect } for  pid=27672 comm="httpd" dest=5671 scontext=system_u:system_r:httpd_t:s0 tcontext=system_u:object_r:amqp_port_t:s0 tclass=tcp_socket permissive=0
```
