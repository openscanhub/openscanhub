# UMB (Unified Message Bus)


## Requesting access to UMB
- instructions:
    - https://mojo.redhat.com/docs/DOC-1072253

- client certificates
    - stage: https://ca02.pki.prod.int.phx2.redhat.com:8443/ca/ee/ca/displayBySerial?serialNumber=268372850
    - prod:  https://ca01.pki.prod.int.phx2.redhat.com:8443/ca/ee/ca/displayBySerial?serialNumber=11672

- tickets requesting access to UMB:
    - stage: RITM0331163
    - prod:  INC0870038


## Debug UMB
```
PN_TRACE_DRV=true ./covscanhub/scripts/umb-emit.py
```

## Watch messages on staging UMB
- using web browser:
    - https://datagrepper.stage.engineering.redhat.com/raw/?category=covscan
