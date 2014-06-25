#!/bin/bash

#
# Script for automatic deploy
#

STAGING_TARGET="root@stage-covscan"
PROFILE_6="eng-rhel-6"

deploy_staging(){
    rm -f ./*.src.rpm
    make srpm || exit 2
    mock --verbose -r ${PROFILE_6} ./*.src.rpm \
        --define "hub_instance stage" \
        --define "hub_host uqtm.lab.eng.brq.redhat.com" \
        || exit 3
    local RPM_NAME
    local RPM_PATH
    RPM_PATH="$(ls /var/lib/mock/${PROFILE_6}/result/covscan-hub-*.noarch.rpm)"
    RPM_NAME="$(basename ${RPM_PATH})"
    rsync ${RPM_PATH} ${STAGING_TARGET}:rpms/
    ssh ${STAGING_TARGET} <<END
yum update -y rpms/${RPM_NAME}
yum reinstall -y rpms/${RPM_NAME}
service httpd restart || :
END
}

case "${1}" in
    stage)
        deploy_staging
        ;;

    *)
        echo $"Usage: ${0} {devel|stage|prod}"
        exit 1
esac

