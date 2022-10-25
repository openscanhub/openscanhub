FROM registry.access.redhat.com/ubi8/ubi

# Internal repositories with all RHEL packages and RCM tools
COPY containers/rhel-8-pulp.repo containers/rcm-tools-for-rhel-8.repo /etc/yum.repos.d/

WORKDIR /src

ENV PYTHONPATH=.:kobo
ENV COVSCAND_CONFIG_FILE=covscand/covscand-local.conf

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
    boost-python3 \
    boost-regex \
    brewkoji \
    cppcheck \
    csmock \
    file \
    gzip \
    koji \
    python3-coverage \
    python3-gssapi \
    python3-six \
    python36 \
    xz

RUN adduser csmock -G mock

# override config_opts['use_bootstrap'] from mock config to make it work in a container
RUN sed -e 's|print_main_output=True"|&, "--no-bootstrap-chroot"|' -i /usr/bin/csmock

RUN adduser coverity -G mock

RUN touch /WORKER_IS_READY

CMD coverage-3.6 run --parallel-mode --omit="*site-packages*,*kobo*," covscand/covscand -f
