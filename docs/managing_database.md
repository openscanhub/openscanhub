# How to manage database

## Connecting to postgres

```
# su -c "psql" - postgres
psql (8.4.20)
Type "help" for help.

postgres=# \connect covscanhub
psql (8.4.20)
You are now connected to database "covscanhub".
```

You can easily list tables:

```
covscanhub=# \dt
                     List of relations
 Schema |            Name             | Type  |   Owner
--------+-----------------------------+-------+------------
 public | auth_group                  | table | covscanhub
 public | auth_group_permissions      | table | covscanhub
 public | auth_message                | table | covscanhub
 public | auth_permission             | table | covscanhub
 public | auth_user                   | table | covscanhub
 public | auth_user_groups            | table | covscanhub
 public | auth_user_user_permissions  | table | covscanhub
 public | django_admin_log            | table | covscanhub
 public | django_content_type         | table | covscanhub
 public | django_session              | table | covscanhub
 public | django_site                 | table | covscanhub
 public | errata_capability           | table | covscanhub
...
```

List schema:

```
covscanhub=# \d auth_user_user_permissions
                              Table "public.auth_user_user_permissions"
     Column      |  Type   |                                Modifiers
-----------------+---------+-------------------------------------------------------------------------
 id              | integer | not null default nextval('auth_user_user_permissions_id_seq'::regclass)
 longnameuser_id | integer | not null
 permission_id   | integer | not null
Indexes:
    "auth_user_user_permissions_pkey" PRIMARY KEY, btree (id)
    "auth_user_user_permissions_user_id_key" UNIQUE, btree (longnameuser_id, permission_id)
    "auth_user_user_permissions_permission_id" btree (permission_id)
    "auth_user_user_permissions_user_id" btree (longnameuser_id)
Foreign-key constraints:
    "auth_user_user_permissions_permission_id_fkey" FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED
    "user_id_refs_id_f2045483" FOREIGN KEY (longnameuser_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED
```

## Resolving database issues quickly

Let's say that database is in inconsistent state, migrations were not applied correctly and we need alter database directly.

The issue:

```
ProgrammingError: column "auth_user_user_permissions.user_id" doesn't exist
```

Can be easily resolved:

```
ALTER TABLE auth_user_user_permissions RENAME COLUMN longnameuser_id TO user_id;
```


Removing `NOT NULL` constraint without migrations:

```
ALTER TABLE auth_user_user_permissions ALTER COLUMN longnameuser_id DROP NOT NULL;
```


## Adding users with longer username than 30 characters

```
>>> p = Permission.objects.get(pk=46)
>>> u2 = User.objects.create(username="errata/errata-web-02.host.qe.eng.pek2.redhat.com@REDHAT.COM")
>>> u2.user_permissions.add(p)
```


## Adding user a permission to submit scans

(prereq is that username is long than 30 chars and thus you can't do this in webui)


```
>>> u = User.objects.get(pk=460)  # id of user we want to edit (can be found in URL in admin interface)
>>> u
<User: errata/errata-web-01.host.qe.eng.pek2.redhat.com>

>>> p = Permission.objects.get(pk=46)  # You can find id in admin's html in forms
>>> p
<Permission: scan | permissions | Can submit ET scan via XML-RPC>
>>> u.user_permissions.add(p)
```

That's all. Now refresh admin interface and see if it's really there.
