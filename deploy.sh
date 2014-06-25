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
        --define "xmlrpc_url https://uqtm.lab.eng.brq.redhat.com/covscanhub/xmlrpc" \
        || exit 3
    local RPM_NAME
    local RPM_PATH
    HUB_RPM_PATH="$(ls /var/lib/mock/${PROFILE_6}/result/covscan-hub-*.noarch.rpm)"
    WORKER_RPM_PATH="$(ls /var/lib/mock/${PROFILE_6}/result/covscan-worker-*.noarch.rpm)"
    HUB_RPM_NAME="$(basename ${HUB_RPM_PATH})"
    WORKER_RPM_NAME="$(basename ${WORKER_RPM_PATH})"
    rsync ${HUB_RPM_PATH} ${WORKER_RPM_PATH} ${STAGING_TARGET}:rpms/
    ssh ${STAGING_TARGET} <<END
yum update -y rpms/${HUB_RPM_NAME} rpms/${WORKER_RPM_NAME}
yum reinstall -y rpms/${HUB_RPM_NAME} rpms/${WORKER_RPM_NAME}
service httpd restart || :
service covscand restart || :
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

