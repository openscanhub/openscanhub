#!/bin/bash

./covscan-xmlrpc-client.py -b wget-1.11.4-4.el6 -t wget-1.12-1.8.el6
./covscan-xmlrpc-client.py -b coreutils-8.4-5.el6 -t coreutils-8.4-19.el6
./covscan-xmlrpc-client.py -b hardlink-1.0-9.el6 -t hardlink-1.0-10.el6
./covscan-xmlrpc-client.py -b NEW_PACKAGE -t tar-1.23-11.el6
