FROM rhel6
RUN set -ex ; \
    cd /etc/yum.repos.d && curl -Ls -O http://cov01.lab.eng.brq.redhat.com/coverity/install/covscan/covscan-rhel-6.repo && \
    curl -sL -O http://download.devel.redhat.com/rel-eng/RCMTOOLS/rcm-tools-rhel-6-server.repo && \
    printf "[latest-rhel6]\nname=latest-rhel6\nbaseurl=http://pulp.dist.prod.ext.phx2.redhat.com/content/dist/rhel/server/6/6Server/x86_64/os/\nenabled=1\ngpgcheck=0\n" >/etc/yum.repos.d/rhel6.repo && \
    yum install -y http://download.eng.brq.redhat.com/pub/fedora/epel/6/x86_64/epel-release-6-8.noarch.rpm && \
    yum install -y --enablerepo=covscan-testing covscan-hub-prod && yum remove -y covscan-hub-prod

RUN yum install -y git

RUN cd /etc && rm -rf ./mock && git clone -b mock git://git.engineering.redhat.com/users/kdudka/coverity-scan.git mock

RUN yum install -y http://download.devel.redhat.com/brewroot/packages/brewkoji/1.9/1.el6eng/noarch/brewkoji-1.9-1.el6eng.noarch.rpm 

RUN adduser coverity && \
    gpasswd -a coverity mock
# we just want hub deps, we will launch hub from git

# setsebool -P httpd_can_network_connect_db 1

COPY . /source

WORKDIR /source

ENV PYTHONPATH=/source/
ENV COVSCAND_CONFIG_FILE=/source/covscand/covscand-local.conf
ENV COVSCAN_CONFIG_FILE=/source/covscan/covscan-local.conf

CMD ["/source/covscanhub/manage.py", "runserver", "0.0.0.0:8000"]
