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

## Debug UMB
```
PN_TRACE_DRV=true ./covscanhub/scripts/umb-emit.py
```

## Watch messages on staging UMB
- using web browser:
    - https://datagrepper.stage.engineering.redhat.com/raw/?category=covscan
