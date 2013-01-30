#!/bin/bash
PKG=`ls *src.rpm`

./covscan/covscan mock-build --config=epel-6-x86_64 --brew-build units-1.87-7.el6 --nowait

./covscan/covscan mock-build --config=epel-6-x86_64 ./$PKG --nowait

./covscan/covscan version-diff-build --base-config=epel-6-x86_64 --config=epel-6-x86_64 --base-srpm=./$PKG --brew-build=units-1.87-7.el6 --all --aggressive --nowait

./covscan/covscan version-diff-build --base-config=epel-6-x86_64 --config=epel-6-x86_64 --base-brew-build=units-1.87-2.fc9 --srpm=./$PKG --concurrency --nowait

./covscan/covscan version-diff-build --base-config=epel-6-x86_64 --config=epel-6-x86_64 --base-brew-build=units-1.87-2.fc9 --brew-build=units-1.87-7.el6 --all --nowait