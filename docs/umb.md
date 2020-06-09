# UMB (Unified Message Bus)


## Requesting access to UMB
- instructions:
    - https://mojo.redhat.com/docs/DOC-1072253

- client certificates
    - stage: https://ca02.pki.prod.int.phx2.redhat.com:8443/ca/ee/ca/displayBySerial?serialNumber=268372850
    - prod:  https://ca02.pki.prod.int.phx2.redhat.com:8443/ca/ee/ca/displayBySerial?serialNumber=268373827

- tickets requesting access to UMB:
    - stage: RITM0331163
    - prod:  INC0870038

- obtaining a client certificate in file:
	- import the certificate into Firefox
	- go to Edit -> Preferences -> Privacy & Security -> View Certificates
	- find the certificate, then click Backup -> msg-client-covscan.p12
	- type passphrase
	- run: openssl pkcs12 -in msg-client-covscan.p12 -nodes -out msg-client-covscan.crt
	- type the same passphrase
	- open msg-client-covscan.crt and manually delete all CA certificates
	- run: { openssl x509 -in msg-client-covscan.crt && openssl rsa -in msg-client-covscan.crt;} > msg-client-covscan.pem

- renewal of the client certificate:
    - go to: https://ca01.pki.prod.int.phx2.redhat.com:8443/ca/ee/ca/profileSelect?profileId=caManualRenewal
    - enter serial ID of the current client certificate and click Submit
    - follow the steps above to obtain the client certificate in file

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
