FROM registry.access.redhat.com/ubi8/ubi

# Internal repository with all RHEL packages
COPY containers/rhel-8-pulp.repo /etc/yum.repos.d/

WORKDIR /src

ENV PYTHONPATH=.:kobo
ENV COVSCAN_CONFIG_FILE=covscan/covscan-local.conf

# Internal CA
RUN cd /etc/pki/ca-trust/source/anchors/ && \
    curl -O https://password.corp.redhat.com/RH-IT-Root-CA.crt && \
    update-ca-trust

RUN echo -e "max_parallel_downloads=20\nfastestmirror=True" >> /etc/dnf/dnf.conf

# epel-release
RUN dnf install -y https://kojipkgs.fedoraproject.org//packages/epel-release/8/13.el8/noarch/epel-release-8-13.el8.noarch.rpm

# internal copr kdudka/mock needed for csmock-core-configs
RUN cd /etc/yum.repos.d/ && curl -O https://copr.devel.redhat.com/coprs/kdudka/mock/repo/epel-8/kdudka-mock-epel-8.repo

RUN dnf -y --setopt=tsflags=nodocs install \
    file \
    gzip \
    python3-coverage \
    python3-koji \
    python3-six \
    python36 \
    xz

# install brew client
RUN dnf install -y --enablerepo=rcm --repofrompath=rcm,http://download.eng.brq.redhat.com/rhel-8/rel-eng/RCMTOOLS/latest-RCMTOOLS-2-RHEL-8/compose/BaseOS/x86_64/os/ --nogpgcheck brewkoji

RUN touch /CLIENT_IS_READY

CMD sleep inf
