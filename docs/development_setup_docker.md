# Development setup of covscan in docker containers


## Hub

```
$ docker build --tag=covscanhub .
$ docker run --net=host -v $PWD:/source:Z --name=hub covscanhub
```

  * You will bind-mount curent sources inside and those will be interpreted,
    it means that you can code and webserver will pick changes on the fly. Neat!

  * --net=host is for getting rid of port mapping/private network nonsense. Trust me,
    it's easier to use host's network for development. You don't need new network stack.

You should be now able to access hub in browser: `http://localhost:8000/`.


### database

We still need a database to set up.

```shell
$ docker exec -ti hub /source/covscanhub/manage.py syncdb --all
```

It's not postgres, but sqlite -- should be easier for development.


Time to load development data into database:

```
$ docker exec -ti hub /source/covscanhub/manage.py loaddata covscanhub/fixtures/development_setup.json
```

Important points:

 * admin/admin is admin acount
 * user/user is regular user account

You may try to access django admin interface:

```
http://covscan-dev/covscanhub/admin/
```

If you need an interactive shell in any of the containers, just run:

```shell
$ docker exec -ti hub bash
```


## worker

```shell
$ docker run -ti --net=host -v $PWD:/source:Z --name=worker covscanhub /source/covscand/covscand -f
```


## client

To test if client is able to connect, let's list available mock configs:

```
docker run --rm -ti --net=host -v $PWD:/source:Z covscanhub /source/covscan/covscan list-mock-configs
```


## configuring analyzers

You can try to submit a build now:

```
$ docker run --rm -ti --net=host -v $PWD:/source:Z covscanhub /source/covscan/covscan mock-build --brew-build curl-7.29.0-25.el7
```

