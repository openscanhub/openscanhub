# Troubleshooting kerberos

 * list principals in keytab: `klist -k /etc/httpd/conf/httpd.keytab`

 * if client can't authenticate, ensure it's using correct hostname (and don't have some bogus entry in `/etc/hosts`)

 * using `curl` to connect to kerberos-guarded endpoint

  ```
  curl --negotiate -u: http://cov01.lab.eng.brq.redhat.com/covscanhub/xmlrpc/kerbauth/
  ```

 * ensure that apache has permissions to read keytab

 * `rdns = false`

 * helpful: [http://www.microhowto.info/howto/configure_apache_to_use_kerberos_authentication.html]

 * also helpful: [http://www.roguelynn.com/words/apache-kerberos-for-django/]

 * perform an xmlrpc post request with curl:

  ```
  curl -s \
       -X POST \
       --header "Content-Type:text/xml" \
       --data "<methodCall><methodName>auth.renew_session</methodName><params></params></methodCall>" \
       --negotiate -u : \
       https://covscan-stage.app.eng.brq.redhat.com/covscanhub/xmlrpc/client/ >res.html
  ```

 * debug kerberos logs on standard output: `env KRB5_TRACE=/dev/stdout`

 * test if kerberos is set up correctly by obtaining TGT using a keytab:

  ```
  env KRB5_TRACE=/dev/stdout kinit -k -t /etc/httpd/conf/httpd.keytab HTTP/covscan-stage.app.eng.brq.redhat.com@REDHAT.COM
  ```
