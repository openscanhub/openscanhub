#!/bin/bash

PKG_VER="covscan-0.3.2"
NVR=$PKG_VER"-1.fc18"
TARBALL=$PKG_VER".tar.bz2"
SRPM=$NVR".src.rpm"
PROFILE1="epel-6-x86_64"
#PROFILE2="fedora-18-x86_64"
DST="`readlink -f "$PWD"`"

make source
#cp /home/ttomecek/dev/covscan/dist/$TARBALL /home/ttomecek/rpmbuild/SOURCES/
rpmbuild -bs "covscan.spec"                     \
    --define "_source_filedigest_algorithm md5" \
    --define "_binary_filedigest_algorithm md5" \
    --define "_sourcedir $DST/dist"             \
    --define "_specdir ."                       \
    --define "_srcrpmdir $DST"                  \


mock -r $PROFILE1 ./$SRPM
#mock -r $PROFILE2 ./SRPMS/$SRPM
