FROM rhel6
RUN set -ex ; \
    cd /etc/yum.repos.d && curl -O http://cov01.lab.eng.brq.redhat.com/coverity/install/covscan/covscan-rhel.repo && \
    printf "[latest-rhel6]\nname=latest-rhel6\nbaseurl=http://pulp.dist.prod.ext.phx2.redhat.com/content/dist/rhel/server/6/6Server/x86_64/os/\nenabled=1\ngpgcheck=0\n" >/etc/yum.repos.d/rhel6.repo && \
    yum install -y http://download.eng.brq.redhat.com/pub/fedora/epel/6/x86_64/epel-release-6-8.noarch.rpm && \
    yum install -y --enablerepo=covscan-testing covscan-hub-prod && yum remove -y covscan-hub-prod

# we just want hub deps, we will launch hub from git

# setsebool -P httpd_can_network_connect_db 1

VOLUME /source

ENV PYTHONPATH=/source/

ENTRYPOINT ["/source/covscanhub/manage.py"]
CMD ["runserver", "0.0.0.0:8000"]
