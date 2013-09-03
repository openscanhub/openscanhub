#!/bin/bash
PKG=`ls *src.rpm`

./covscan/covscan mock-build --config=epel-6-x86_64 --brew-build units-1.87-7.el6 --nowait

./covscan/covscan mock-build --config=epel-6-x86_64 ./$PKG --nowait

./covscan/covscan version-diff-build --base-config=epel-6-x86_64 --config=epel-6-x86_64 --base-srpm=./$PKG --brew-build=units-1.87-7.el6 --all --aggressive --nowait

./covscan/covscan version-diff-build --base-config=epel-6-x86_64 --config=epel-6-x86_64 --base-brew-build=units-1.87-2.fc9 --srpm=./$PKG --concurrency --nowait

./covscan/covscan version-diff-build --base-config=epel-6-x86_64 --config=epel-6-x86_64 --base-brew-build=units-1.87-2.fc9 --brew-build=units-1.87-7.el6 --all --nowait

# --analyzer option

./covscan/covscan mock-build --config=epel-6-x86_64 -a cov-6.6.1,clang,cppcheck -w 3 --brew-build hardlink-1.0-10.el6
./covscan/covscan mock-build --config=epel-6-x86_64 -l --brew-build hardlink-1.0-10.el6
./covscan/covscan mock-build --config=epel-6-x86_64 -l -c -w 2 --brew-build hardlink-1.0-10.el6
./covscan/covscan mock-build --config=epel-6-x86_64 -b -w 3 --brew-build hardlink-1.0-10.el6
./covscan/covscan mock-build --config=epel-6-x86_64 -a cov-x --brew-build hardlink-1.0-10.el6
./covscan/covscan mock-build --config=epel-6-x86_64 -a cov-6.6.1,cov6.5.3 --brew-build hardlink-1.0-10.el6
./covscan/covscan mock-build --config=epel-6-x86_64 -a cov-6.6.1,cov-6.5.3 --brew-build hardlink-1.0-10.el6
./covscan/covscan mock-build --config=epel-6-x86_64 -a cov-6.6.1,clang,cppcheck -w 3 --brew-build dracut-032-1.fc20
./covscan/covscan mock-build --config=fedora-20-x86_64 -a cov-6.6.1,clang,cppcheck -b -c -l --brew-build dracut-032-1.fc20

