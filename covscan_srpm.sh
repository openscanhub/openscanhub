#!/bin/bash

PKG_VER="covscan-0.2.2"
NVR=$PKG_VER"-1.fc17"
TARBALL=$PKG_VER".tar.bz2"
SRPM=$NVR".src.rpm"
PROFILE1="epel-6-x86_64"
#PROFILE2="fedora-17-x86_64"

cp /home/ttomecek/dev/covscan/dist/$TARBALL /home/ttomecek/rpmbuild/SOURCES/
rpmbuild -bs SPECS/covscan.spec --define "_source_filedigest_algorithm md5" --define "_binary_filedigest_algorithm md5"
mock -r $PROFILE1 ./SRPMS/$SRPM
#mock -r $PROFILE2 ./SRPMS/$SRPM
