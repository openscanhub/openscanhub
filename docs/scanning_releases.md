# How covscan handles requests from Errata Tool

This document shows how covscan picks proper mock profile and what changes should be performed in order to scan arbitrary packages from various components.


Here's a scan request from Errata Tool:

```
{
  "errata_id": 22986,
  "target": "ceph-10.1.0-1.el7cp",
  "base": "NEW_PACKAGE",
  "rhel_version": "RHEL-7",
  "release": "CEPH-2.0",
  "package_owner": "kdreyer",
  "id": 14960
}
```

Let me explain what it means: covscan is suppose to scan package `ceph-10.1.0-1.el7cp`, which is a newly added package (base is `NEW_PACKAGE`). It's part of product `CEPH-2.0` and built on top of RHEL 7. Bad thing is that covscan ignores `rhel_version`.

In order to scan this, covscan translates `release`. Translation rules can be found in **Release mappings** table:

```
Id   Release tag              Template            Priority
1    ^RHEL-(\d+)\.(\d+)\.0$   RHEL-%s.%s          1
2    ^FAST(\d+)\.(\d+)$       RHEL-%s.%s          2
3    ^CEPH-(\d+)\.(\d+).*$    RHEL-7-CEPH-%s-%s   3
```

In case of this request, `CEPH-2.0` gets translated to `RHEL-7-CEPH-2-0`.

Let's move to table **Tags** now:

```
Id   Brew tag           Mock            Release
48   RHEL-7-CEPH-2-0    rhel-7-x86_64   rhel-7.1 -- Red Hat Enterprise Linux 7.1
```

As you can see, we have `RHEL-7-CEPH-2-0` here. And that's exactly what's being picked after translation.

Therefore, `CEPH-2.0` is being scanned in `rhel-7-x86_64` mock profile.

