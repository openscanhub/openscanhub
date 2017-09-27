#!/bin/bash

#
# Script for automatic deploy
#

STAGING_TARGET="root@stage-covscan"
STAGING2_TARGET="root@covscan-stage.lab.eng.brq2.redhat.com"
PROD_TARGET="cov01"
PROD_TARGET2="ttomecek@cov02"
COV02_TARGET="root@cov02"
PROFILE_6="eng-rhel-6"

INSTANCE=""
TARGET=""
HOST=""

deploy_staging(){
    rm -f ./*.src.rpm
    make srpm || exit 2
    mock --verbose -r ${PROFILE_6} ./*.src.rpm \
        --define "hub_instance ${INSTANCE}" \
        --define "hub_host ${HOST}" \
        --define "xmlrpc_url https://${HOST}/covscanhub/xmlrpc" \
        || exit 3
    HUB_RPM_PATH="$(ls /var/lib/mock/${PROFILE_6}/result/covscan-hub-*.noarch.rpm)"
    WORKER_RPM_PATH="$(ls /var/lib/mock/${PROFILE_6}/result/covscan-worker-*.noarch.rpm)"
    HUB_RPM_NAME="$(basename ${HUB_RPM_PATH})"
    WORKER_RPM_NAME="$(basename ${WORKER_RPM_PATH})"
    cp -a ${HUB_RPM_PATH} ./deploy/
    cp -a ${WORKER_RPM_PATH} ./deploy/
    rsync ./deploy/${HUB_RPM_NAME} ./deploy/${WORKER_RPM_NAME} ${TARGET}:rpms/
    ssh ${TARGET} <<END
yum update -y rpms/${HUB_RPM_NAME} rpms/${WORKER_RPM_NAME}
yum install -y rpms/${HUB_RPM_NAME} rpms/${WORKER_RPM_NAME}
service httpd restart || :
service covscand restart || :
END
}

deploy_prod(){
    rm -f ./*.src.rpm
    make srpm || exit 2
    mock --verbose -r ${PROFILE_6} ./*.src.rpm \
        --define "hub_instance prod" \
        --define "hub_host cov01.lab.eng.brq.redhat.com" \
        --define "xmlrpc_url http://cov01.lab.eng.brq.redhat.com/covscanhub/xmlrpc" \
        || exit 3
    HUB_RPM_PATH="$(ls /var/lib/mock/${PROFILE_6}/result/covscan-hub-*.noarch.rpm)"
    WORKER_RPM_PATH="$(ls /var/lib/mock/${PROFILE_6}/result/covscan-worker-*.noarch.rpm)"
    HUB_RPM_NAME="$(basename ${HUB_RPM_PATH})"
    WORKER_RPM_NAME="$(basename ${WORKER_RPM_PATH})"
    rsync ${HUB_RPM_PATH} ${WORKER_RPM_PATH} ${PROD_TARGET}:ttomecek/rpms/
    rsync ${WORKER_RPM_PATH} ${PROD_TARGET2}:rpms/
#    ssh ${PROD_TARGET} <<END
#yum update -y rpms/${HUB_RPM_NAME} rpms/${WORKER_RPM_NAME}
#yum reinstall -y rpms/${HUB_RPM_NAME} rpms/${WORKER_RPM_NAME}
#service httpd restart || :
#service covscand restart || :
#END
}

case "${1}" in
    prod)
        deploy_prod
        ;;

    stage)
        TARGET="root@stage-covscan"
        HOST="covscan-stage.lab.eng.brq2.redhat.com"
        INSTANCE="stage"
        deploy_staging
        ;;

    stage2)
        TARGET="root@covscan-stage.lab.eng.brq2.redhat.com"
        HOST="covscan-stage.lab.eng.brq2.redhat.com"
        INSTANCE="stage"
        deploy_staging
        ;;

    *)
        echo $"Usage: ${0} {devel|stage|prod}"
        exit 1
esac

