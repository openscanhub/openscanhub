FROM registry.access.redhat.com/ubi8/ubi

EXPOSE 8000

# Internal repositories with all RHEL packages and RCM tools
COPY containers/rhel-8-pulp.repo containers/rcm-tools-for-rhel-8.repo /etc/yum.repos.d/

WORKDIR /src

ENV PYTHONPATH=.:kobo

RUN echo -e "max_parallel_downloads=20\nfastestmirror=True" >> /etc/dnf/dnf.conf

# Internal CA
RUN cd /etc/pki/ca-trust/source/anchors/ && \
    curl -O https://password.corp.redhat.com/RH-IT-Root-CA.crt && \
    update-ca-trust

# epel-release
RUN dnf install -y https://kojipkgs.fedoraproject.org//packages/epel-release/8/13.el8/noarch/epel-release-8-13.el8.noarch.rpm

# internal copr kdudka/mock needed for csmock-core-configs (mock configs are required by unit tests)
RUN cd /etc/yum.repos.d/ && curl -O https://copr.devel.redhat.com/coprs/kdudka/mock/repo/epel-8/kdudka-mock-epel-8.repo

# enable installation of gettext message objects
RUN rm /etc/rpm/macros.image-language-conf

RUN dnf -y --setopt=tsflags=nodocs install \
    /usr/bin/krb5-config \
    boost-program-options \
    boost-python3 \
    boost-regex \
    brewkoji \
    cpio \
    csdiff \
    csmock \
    gcc \
    glibc-langpack-en \
    gzip \
    python3-bugzilla \
    python3-coverage \
    python3-csdiff \
    python3-devel \
    python3-django3 \
    python3-gssapi \
    python3-jira \
    python3-koji \
    python3-psycopg2 \
    python3-qpid-proton \
    python36 \
    postgresql{,-libs} \
    xz

COPY containers/hub/run.sh /run.sh
RUN chmod +x /run.sh

CMD /run.sh
